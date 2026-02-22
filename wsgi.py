"""
WSGI config for mandale project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mandale_project.settings')

application = get_wsgi_application()
