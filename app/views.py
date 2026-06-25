import os
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from .services.analyzer_service import get_ai_analysis # Updated import path

def home(request):
    return render(request, 'home.html')

def upload_resume(request):
    if request.method == 'POST' and 'resume' in request.FILES:
        # Simulate analysis for now
        return JsonResponse({'analysis': 'This is a simulated AI analysis result.'})
    return JsonResponse({'error': 'Invalid request'}, status=400)
