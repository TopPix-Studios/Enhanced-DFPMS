from django.utils.translation import gettext_lazy as _
from jet.dashboard import modules
from jet.dashboard.dashboard import Dashboard
from .dashboard_modules import ChartModule  # Import the custom chart module

class CustomIndexDashboard(Dashboard):
    columns = 3 
  
    def init_with_context(self, context):
        self.available_children.append(modules.LinkList)
        self.available_children.append(ChartModule)  # Make ChartModule available

        self.children.append(modules.LinkList(
            _('Support'),
            children=[
                {
                    'title': _('Django documentation'),
                    'url': 'http://docs.djangoproject.com/',
                    'external': True,
                },
                {
                    'title': _('Django "django-users" mailing list'),
                    'url': 'http://groups.google.com/group/django-users',
                    'external': True,
                },
                {
                    'title': _('Django irc channel'),
                    'url': 'irc://irc.freenode.net/django',
                    'external': True,
                },
            ],
            column=0,
            order=0
        ))

        # Add the custom chart module
        self.children.append(ChartModule(
            column=1,
            order=0
        ))
