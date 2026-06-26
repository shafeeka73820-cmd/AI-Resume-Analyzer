from django.shortcuts import render
import json
import os
import re
import uuid
import pdfplumber
from docx import Document
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .utils import calculate_ats_score, generate_roadmap, generate_skill_improvement_plan

def home(request):
    return render(request, 'home.html')

# ... rest of your code


def _parse_pdf_to_roadmap(text, name):
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 3]
    skip_headers = {'related roadmaps', 'roadmap.sh', 'find the detailed', 'along with other'}
    filtered = [l for l in lines if not any(h in l.lower() for h in skip_headers)]
    if not filtered:
        filtered = lines

    n = len(filtered)
    if n == 0:
        return [{'month': 'Month 1', 'title': 'Roadmap Overview', 'items': ['No content extracted from PDF']}]

    chunk_size = max(n // 3, 1)
    chunks = [filtered[i:i + chunk_size] for i in range(0, n, chunk_size)]
    while len(chunks) < 3:
        chunks.append([])
    chunks = chunks[:3]

    titles = ['Foundations & Core Concepts', 'Tools & Hands-on Practice', 'Advanced Topics & Portfolio']
    months = []
    for i, chunk in enumerate(chunks):
        items = chunk[:15] if chunk else ['Open the PDF to view full roadmap details']
        months.append({'month': f'Month {i + 1}', 'title': titles[i], 'items': items})
    return months


def load_sample_roadmaps():
    import re
    samples_dir = Path(settings.BASE_DIR).parent / 'samples'
    roadmaps = []
    if not samples_dir.exists():
        return roadmaps
    for f in sorted(samples_dir.glob('*.json')):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            name = f.stem.replace('-', ' ').replace('_', ' ').title()
            roadmaps.append({'name': name, 'filename': f.name, 'url': f'/api/samples/{f.name}'})
        except Exception as e:
            print(f'Failed to load roadmap {f.name}: {e}')
    for f in sorted(samples_dir.glob('*.pdf')):
        try:
            text = extract_text_from_pdf(str(f))

            if 'roadmap' not in text.lower():
                continue

            name = f.stem.replace('-', ' ').replace('_', ' ').title()
            roadmaps.append({'name': name, 'filename': f.name, 'url': f'/api/samples/{f.name}'})
        except Exception as e:
            print(f'Failed to load roadmap PDF {f.name}: {e}')
    return roadmaps

try:
    from supabase import create_client
    supabase = create_client(
        os.getenv('SUPABASE_URL', ''),
        os.getenv('SUPABASE_ANON_KEY', '')
    )
except Exception:
    supabase = None


def extract_text_from_pdf(file_path):
    text = ''
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    return text


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return '\n'.join(p.text for p in doc.paragraphs)


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def sample_roadmap_file(request, filename):
    samples_dir = Path(settings.BASE_DIR).parent / 'samples'
    file_path = samples_dir / filename
    if not file_path.exists() or not file_path.is_file():
        from django.http import JsonResponse
        return JsonResponse({'error': 'File not found'}, status=404)
    from django.http import FileResponse
    resp = FileResponse(open(file_path, 'rb'), filename=filename, content_type='application/pdf')
    resp['X-Frame-Options'] = 'ALLOWALL'
    resp['Access-Control-Allow-Origin'] = '*'
    return resp


@api_view(['POST'])
def upload_file(request):
    file = request.FILES.get('resume')
    if not file:
        return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

    max_size = 5 * 1024 * 1024
    if file.size > max_size:
        return Response({'error': 'File size exceeds 5MB limit'}, status=status.HTTP_400_BAD_REQUEST)

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ('.pdf', '.docx'):
        return Response({'error': 'Only PDF and DOCX files are allowed'}, status=status.HTTP_400_BAD_REQUEST)

    filename = f'{datetime.now().timestamp()}-{file.name}'
    file_path = os.path.join(settings.BASE_DIR, 'uploads', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb') as f:
        f.write(file.read())
    full_path = file_path

    try:
        if ext == '.pdf':
            text = extract_text_from_pdf(full_path)
        else:
            text = extract_text_from_docx(full_path)
    except Exception as e:
        os.remove(full_path)
        return Response({'error': f'Failed to parse file: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    os.remove(full_path)
    return Response({'text': text, 'filename': file.name})


@api_view(['POST'])
def analyze_resume(request):
    resume_text = request.data.get('resumeText')
    job_description = request.data.get('jobDescription', '') or 'general software engineering role'
    user_email = request.data.get('userEmail', 'anonymous@example.com')
    resume_name = request.data.get('resumeName', 'resume.pdf')

    if not resume_text:
        return Response(
            {'error': 'resumeText is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = calculate_ats_score(resume_text, job_description)
    roadmap = generate_roadmap(result['missing_keywords'], resume_text, job_description)
    skill_improvement = generate_skill_improvement_plan(resume_text, result['missing_keywords'])
    sample_roadmaps = load_sample_roadmaps()

    analysis = {
        'id': str(uuid.uuid4()),
        'user_email': user_email,
        'resume_name': resume_name,
        'ats_score': result['ats_score'],
        'matched_keywords': result['matched_keywords'],
        'missing_keywords': result['missing_keywords'],
        'suggestions': result['suggestions'],
        'breakdown': result['breakdown'],
        'roadmap': roadmap,
        'skill_improvement': skill_improvement,
        'sample_roadmaps': sample_roadmaps,
    }

    if supabase:
        try:
            supabase.table('analyses').insert({
                'id': analysis['id'],
                'user_email': analysis['user_email'],
                'resume_name': analysis['resume_name'],
                'ats_score': analysis['ats_score'],
                'job_description': job_description,
                'matched_keywords': analysis['matched_keywords'],
                'missing_keywords': analysis['missing_keywords'],
                'suggestions': analysis['suggestions'],
                'created_at': datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            print(f'Supabase insert warning: {e}')

    return Response(analysis)


@api_view(['GET'])
def list_roadmaps(request):
    samples_dir = Path(settings.BASE_DIR) / 'samples'
    roadmaps = []
    if samples_dir.exists():
        for f in sorted(samples_dir.glob('*.json')):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                if 'phases' in data and 'name' in data:
                    data['filename'] = f.name
                    roadmaps.append(data)
            except Exception:
                pass
    return Response(roadmaps)


@api_view(['GET'])
def get_roadmap(request, filename):
    samples_dir = Path(settings.BASE_DIR) / 'samples'
    file_path = samples_dir / filename
    if not file_path.exists() or not file_path.is_file():
        return Response({'error': 'Roadmap not found'}, status=404)
    try:
        data = json.loads(file_path.read_text(encoding='utf-8'))
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()})
