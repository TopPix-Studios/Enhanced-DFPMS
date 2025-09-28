from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.sites.models import Site
from django.templatetags.static import static
from django.core.signing import TimestampSigner
from django.urls import reverse
from django.utils.http import urlencode
from django.conf import settings
from django.core.signing import dumps
from .models import Profile
from django.contrib.sites.models import Site
from django.contrib import messages

def send_profile_missing_email(user):
    current_site = Site.objects.get_current()
    logo_url = f"{current_site.domain}{static('img/General_Santos_City_seal.jpg')}"
    login_url = f"{current_site.domain}/login/"  # or your actual login URL

    context = {
        'user': user,
        'login_url': login_url,
        'site_name': 'Profiling System',
        'logo_url': logo_url,
    }

    html_message = render_to_string('components/profile_missing_email.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        'Action Required: Complete Your Profile',
        plain_message,
        'gensanity.information@gmail.com',
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )
def send_profile_incomplete_email(user, missing_items, edit_link_base):
    signer = TimestampSigner()
    profile = Profile.objects.get(account_id=user.account_id)
    df_id = profile.df_id
    data = dumps({
        'df_id': df_id,
        'missing_items': missing_items
    })
    signed_token = signer.sign(data)

    edit_link = edit_link_base  # ✅ Use full link passed from generate_secure_edit_link
    current_site = Site.objects.get_current()
    logo_url = f"https://{current_site.domain}{static('img/General_Santos_City_seal.jpg')}"
    context = {
        'user': user,
        'missing_items': missing_items,
        'edit_link': edit_link,
        'site_name': 'Profiling System',
        'logo_url': logo_url,
    }

    html_message = render_to_string('components/profile_incomplete_email.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        'Action Required: Complete Your Profile',
        plain_message,
        'gensanity.information@gmail.com',
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

def generate_secure_edit_link(profile, missing_items):
    signer = TimestampSigner()
    payload = dumps({
        'df_id': profile.df_id,
        'missing_items': missing_items
    })
    signed_token = signer.sign(payload)

    query = urlencode({'token': signed_token})
    url = f"{settings.SITE_URL}{reverse('edit_resume_projects', args=[profile.df_id])}?{query}"
    return url


