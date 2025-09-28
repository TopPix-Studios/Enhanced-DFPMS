from django.utils.deprecation import MiddlewareMixin
from .models import Log
from django.contrib.contenttypes.models import ContentType

class LogRequestMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Only log if the user is authenticated, you can remove this condition if you want to log for all users
        user = request.user if request.user.is_authenticated else None
        
        # Get the URL and view name
        url = request.path
        view_name = request.resolver_match.view_name if request.resolver_match else 'Unknown view'

        # Log the access
        Log.objects.create(
            user=user,
            action='access',
            url=url,
            view_name=view_name,
            message=f"User accessed {url}",
        )
        return None  # Let the view proceed as normal
