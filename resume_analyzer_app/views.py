from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .ai_service import get_ai_analysis
import json
from reportlab.pdfgen import canvas
import io
from pypdf import PdfReader

# Rectified home view to render home.html
def home(request):
    return render(request, 'home.html')

def analyze_resume(request):
    # Nee resume analysis code ikkada untadi
    return JsonResponse({"result": "Analysis complete"})

def upload_resume(request):
    analysis = None
    if request.method == 'POST' and 'resume' in request.FILES:
        resume = request.FILES['resume']
        
        # Real PDF Parsing
        try:
            reader = PdfReader(resume)
            resume_text = ""
            for page in reader.pages:
                resume_text += page.extract_text() + "\n"
        except:
            resume_text = "Could not parse PDF"
            
        # Call AI
        ai_response = get_ai_analysis(resume_text)
        
        # Parse JSON from AI
        try:
            analysis = json.loads(ai_response.replace('```json', '').replace('```', ''))
        except:
            analysis = {"error": "AI response parsing failed"}
        
        # Save to session
        request.session['last_analysis'] = analysis
            
    return render(request, 'resume_analyzer_app/upload.html', {'analysis': analysis})

def analyze_resume_api(request):
    return HttpResponse("API Endpoint Placeholder", status=200)

def export_pdf(request):
    analysis = request.session.get('last_analysis')
    if not analysis:
        return HttpResponse("No analysis found", status=404)
        
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, "Resume Analysis Report")
    
    # Safely get ATS score
    score = analysis.get('ats_score', 'N/A')
    p.drawString(100, 780, f"ATS Score: {score}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')
