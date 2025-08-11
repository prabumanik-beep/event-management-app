# c:\Users\263561\Event Management\scheduling\apps.py
from django.apps import AppConfig

class SchedulingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduling'

    def ready(self):
        pass # No need to import signals here
