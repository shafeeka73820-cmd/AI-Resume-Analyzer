import os
import sys

# Add the project directory to the sys.path
path = '/home/your_username/ai-resume-analyzer'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


from django.core.wsgi import get_wsgi_application
app= get_wsgi_application()
