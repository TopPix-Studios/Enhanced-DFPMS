from django.apps import AppConfig

class ProfilingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profiling'

    def ready(self):
        import profiling.signals
        # import profiling.dashboard_modules
        # import profiling.dashboard
