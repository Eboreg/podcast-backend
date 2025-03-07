"""
ASGI config for main project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

import dotenv
from django.core.asgi import get_asgi_application


dotenv.load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_asgi_application()
