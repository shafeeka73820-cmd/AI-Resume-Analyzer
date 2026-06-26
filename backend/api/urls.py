from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='api-root'), # Added root path for /api/
    path('upload', views.upload_file, name='upload-file'),
    path('analyze', views.analyze_resume, name='analyze-resume'),
    path('health', views.health_check, name='health-check'),
    path('samples/<str:filename>', views.sample_roadmap_file, name='sample-roadmap-file'),
    path('roadmaps', views.list_roadmaps, name='list-roadmaps'),
    path('roadmaps/<str:filename>', views.get_roadmap, name='get-roadmap'),
]
