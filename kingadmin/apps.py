from django.apps import AppConfig
from django.contrib.admin import autodiscover_modules


class KingadminConfig(AppConfig):
    name = 'kingadmin'

    def ready(self):
        autodiscover_modules("kingadmin")
