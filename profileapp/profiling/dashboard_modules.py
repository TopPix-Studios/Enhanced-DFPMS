from jet.dashboard.modules import DashboardModule
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.apps import apps

class ChartModule(DashboardModule):
    title = _('Skills Distribution')
    template = 'admin/custom_chart_module.html'

    def init_with_context(self, context):
        Skills = apps.get_model('profiling', 'Skills')
        BackgroundInformation = apps.get_model('profiling', 'BackgroundInformation')

        # Count the number of people who have each skill
        skill_counts = BackgroundInformation.objects.values('skills__skill').annotate(count=Count('skills')).order_by('-count')
        
        labels = [entry['skills__skill'] for entry in skill_counts]
        values = [entry['count'] for entry in skill_counts]
        
        context.update({
            'labels': labels,
            'values': values
        })
