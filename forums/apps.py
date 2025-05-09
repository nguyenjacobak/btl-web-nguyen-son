from django.apps import AppConfig


class YourAppConfig(AppConfig):
    name = 'forums'

    def ready(self):
        import forums.signals