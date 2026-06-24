from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .ai_service import get_ai_analysis
import json

# Home view to render the upload page
def home(request):
    return render(request, 'home.html')

def upload_resume(request):
    analysis = None
    error_msg = None
    if request.method == 'POST' and 'resume' in request.FILES:
        try:
            resume = request.FILES['resume']
            
            # Simulated text reading for now to avoid PDF library issues on Vercel
            resume_text = "Simulated resume text. User uploaded: " + resume.name
            
            # Call AI
            ai_response = get_ai_analysis(resume_text)
            
            # Parse JSON from AI
            try:
                analysis = json.loads(ai_response.replace('```json', '').replace('```', ''))
            except:
                error_msg = "AI response parsing failed"
        except Exception as e:
            error_msg = str(e)
            
    return render(request, 'home.html', {'analysis': analysis, 'error': error_msg})

def analyze_resume_api(request):
    return HttpResponse("API Endpoint Placeholder", status=200)

def export_pdf(request):
    return HttpResponse("PDF export temporarily disabled", status=501)
