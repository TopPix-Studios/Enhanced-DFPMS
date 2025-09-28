from django.shortcuts import render,  redirect, get_object_or_404
from django.views.generic.edit import FormView
from django.contrib.auth import authenticate, login, get_backends
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.utils.html import format_html
from django.http import HttpResponseBadRequest
from .forms import CustomAuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from .models import Account, Province, City, Barangay, Region, Certificate, PastExperience, Tag, Resume, BackgroundInformationLanguage, BackgroundInformation, Event, Profile, Country, Project, Attendance
from events.models import Event, RSVP, Attendance, Announcement
from support.models import Notification
from django.forms import modelformset_factory
from support.models import SupportTicket, Message
from .forms import AccountForm, ProfileForm, UpdateLanguageForm, MessageForm, BackgroundInformationForm, CertificateForm, ProjectForm, ResumeForm, GuestAttendanceForm, UpdateProfileForm, PastExperienceFormSet, ProjectFormSet, UpdateBackgroundInformationForm, LanguageForm, SkillsForm, PastExperienceForm
from django.contrib.auth.decorators import login_required
from datetime import date
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
import json
from .models import Language, Skills
from django.core.serializers import serialize
from datetime import date, timedelta
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount import app_settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .forms import PasswordResetForm, SetPasswordForm
from collections import defaultdict
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.db.models import Max  # Import Max
import base64
from io import BytesIO
from django.core.files.storage import FileSystemStorage
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.signing import loads
from django.contrib.sites.shortcuts import get_current_site  # ✅ for dynamic domain
from django.utils.http import urlencode

def index(request):
    if request.user.is_authenticated:
        # Redirect staff users to the Django admin panel
        if request.user.is_staff:
            return redirect(reverse('admin:index'))

        # Check if the user is verified
        if hasattr(request.user, 'is_verified') and not request.user.is_verified:
            messages.info(request, 'Your account is pending verification by the admin. Please wait.')
            logout(request)
            return redirect('index')  # redirect back to index as anonymous user

        # Redirect verified users to their profile detail page
        return redirect(reverse('profile_detail'))

    # Render landing/index page for anonymous users
    return render(request, 'index.html')

def about_us(request):
    if request.user.is_authenticated:
        # Assuming account_id is an attribute of the related profile model
        user_account_id = request.user.account_id
        # Redirect to the profile detail view with the user_account_id
        return redirect(reverse('about_us_logined'))
    
    return render(request, 'about.html')

def about_us_logined(request):
    account_id = request.user.account_id
    
    try:
        user_profile = Profile.objects.get(account_id=account_id)
    except Profile.DoesNotExist:
        return redirect('create_profile')

    context = {
        'profile': user_profile,
    }
    return render(request, 'components/about_logined.html', context)

def privacy_policy(request):
    if request.user.is_authenticated:
        # Assuming account_id is an attribute of the related profile model
        user_account_id = request.user.account_id
        # Redirect to the profile detail view with the user_account_id
        return redirect(reverse('privacy_policy_logined'))
    
    return render(request, 'privacy_policy.html')

def privacy_policy_logined(request):
    account_id = request.user.account_id
    try:
        user_profile = Profile.objects.get(account_id=account_id)
    except Profile.DoesNotExist:
        return redirect('create_profile')

    context = {
        'profile': user_profile,
    }
    return render(request, 'components/privacy_policy_logined.html', context)

def guest_announcement(request):
      # Check if the user is authenticated
    if request.user.is_authenticated:
        # Assuming account_id is an attribute of the related profile model
        user_account_id = request.user.account_id
        # Redirect to the profile detail view with the user_account_id
        return redirect(reverse('profile_detail'))
    
    return render(request, 'guest_announcement.html')

def send_password_reset_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = settings.SITE_URL  # Add your site URL in settings
    password_reset_url = f"{current_site}/reset/{uid}/{token}/"

    context = {
        'email': user.email,
        'domain': current_site,
        'site_name': 'Profiling System',
        'uid': uid,
        'user': user,
        'token': token,
        'password_reset_url': password_reset_url,
    }

    html_message = render_to_string('components/password_reset_email.html', context)
    plain_message = strip_tags(html_message)
    from_email = 'gensanity.information@gmail.com'
    to = user.email

    send_mail(
        'Password Reset Requested',
        plain_message,
        from_email,
        [to],
        html_message=html_message,
        fail_silently=False,
    )

def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = Account.objects.filter(email=email)
            if associated_users.exists():
                for user in associated_users:
                    send_password_reset_email(user)
                messages.success(request, 'A link to reset your password has been sent to your email.')
                return redirect('password_reset_done')
    form = PasswordResetForm()
    return render(request=request, template_name="components/password_reset.html", context={"form": form})

def password_reset_done(request):
    return render(request=request, template_name="components/password_reset_done.html")

def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                messages.success(request, 'Your password has been set. You can now log in.')
                return redirect('user_login')
        else:
            form = SetPasswordForm()
        return render(request, 'components/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('password_reset')
    
def guest_announcement_view(request):
      # Check if the user is authenticated
    if request.user.is_authenticated:
        # Assuming account_id is an attribute of the related profile model
        user_account_id = request.user.account_id
        # Redirect to the profile detail view with the user_account_id
        return redirect(reverse('profile_detail'))
    
    return render(request, 'guest_announcement_view.html')

def guest_event(request):
      # Check if the user is authenticated
    if request.user.is_authenticated:
        # Assuming account_id is an attribute of the related profile model
        user_account_id = request.user.account_id
        # Redirect to the profile detail view with the user_account_id
        return redirect(reverse('profile_detail'))

    current_date = date.today()
    
    search_query = request.GET.get('search', '')
    tag_filter = request.GET.get('tag', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    events = Event.objects.all()


    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) 
        )

    if tag_filter:
        events = events.filter(tags__id=tag_filter)

    if start_date:
        events = events.filter(start_datetime__gte=start_date)

    if end_date:
        events = events.filter(start_datetime__lte=end_date)

    events_today = events.filter(start_datetime__date=current_date).order_by('-start_datetime')
    all_events = events.order_by('-start_datetime')
    upcoming_events = events.filter(start_datetime__date__gte=current_date).order_by('start_datetime')

    sort = request.GET.get('sort')

    if sort == 'latest':
        all_events =  all_events.order_by('-created_at')
    elif sort == 'oldest':
        all_events =  all_events.order_by('created_at')
 
   
    # Paginator for today's events
    paginator_today = Paginator(events_today, 10)
    page_number_today = request.GET.get('page_today')
    page_obj_today = paginator_today.get_page(page_number_today)

    # Paginator for past events
    paginator_past = Paginator(all_events, 10)
    page_number_past = request.GET.get('page_past')
    page_obj_past = paginator_past.get_page(page_number_past)

    # Paginator for upcoming events
    paginator_upcoming = Paginator(upcoming_events, 10)
    page_number_upcoming = request.GET.get('page_upcoming')
    page_obj_upcoming = paginator_upcoming.get_page(page_number_upcoming)

    # Get unread notifications

    all_tags = Tag.objects.all()



    context = {
        'page_obj_today': page_obj_today,
        'page_obj_past': page_obj_past,
        'page_obj_upcoming': page_obj_upcoming,
        'current_date': current_date,
        'all_tags': all_tags,
        'sort':sort,
    }
    
    return render(request, 'guest_event.html', context)

def guest_event_attendance(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = GuestAttendanceForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            age_range = form.cleaned_data['age_range']
            gender = form.cleaned_data['gender']
            pwd = form.cleaned_data['pwd']
            four_ps = form.cleaned_data['four_ps']
            affiliation = form.cleaned_data['affiliation']
            contact = form.cleaned_data['contact']
            email = form.cleaned_data['email']

            current_time = timezone.now()

            if current_time < event.start_datetime:
                messages.error(request, f"{event.title} has not started yet. It will start on {event.start_datetime}.")
            elif current_time > event.end_datetime:
                messages.error(request, f"{event.title} has ended on {event.end_datetime}.")
            else:
                attendance, created = Attendance.objects.get_or_create(
                    event=event, name=name, defaults={
                        'age_range': age_range,
                        'gender': gender,
                        'pwd': pwd,
                        'four_ps': four_ps,
                        'affiliation': affiliation,
                        'contact': contact,
                        'email': email
                    }
                )
                if created:
                    attendance.logged_in = False
                    attendance.save()
                messages.success(request, f"You have successfully registered for {event.title}.")

            return redirect('index')
    else:
        form = GuestAttendanceForm()
        
    return render(request, 'guest_event_attendance.html', {'form': form, 'event': event})

def otp_verification(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        otp = data.get('otp')
        
        if not user_id or not otp:
            return JsonResponse({'status': 'failed', 'message': 'User ID or OTP is missing'})

        user = get_object_or_404(Account, account_id=user_id)

        if user.verify_otp(otp):
            user.is_verified = True
            user.last_login_date = timezone.now()
            user.save()
            backend_path = 'django.contrib.auth.backends.ModelBackend'  # Specify the backend path as a string
            login(request, user, backend=backend_path)
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'failed', 'message': 'Invalid OTP'})
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'})


def resend_otp(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'failed', 'message': 'Invalid request method'})

    data = json.loads(request.body)
    user = get_object_or_404(Account, account_id=data.get('user_id'))

    # Only throttle if user.last_login_date exists
    if user.last_login_date:
        elapsed = (timezone.now() - user.last_login_date).total_seconds()
        if elapsed < 60:
            wait = int(60 - elapsed)
            return JsonResponse({
                'status': 'failed',
                'message': f'Please wait {wait} more second{"s" if wait>1 else ""} before resending OTP'
            })

    otp = user.generate_otp()

    # Get current domain, e.g. '127.0.0.1:8000' or 'yourdomain.com'
    domain = get_current_site(request).domain
    
    # Render email with absolute image path
    html_message = render_to_string('components/otp_email.html', {
        'otp': otp,
        'domain': domain  # Pass domain to template
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject='Your OTP Code',
        message=plain_message,
        from_email='gensanity.information@gmail.com',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    user.last_login_date = timezone.now()
    user.save(update_fields=['last_login_date'])
    return JsonResponse({'status': 'success'})

def user_login(request):
    if request.user.is_authenticated:
        user = request.user

        try:
            profile = Profile.objects.get(account_id=user)

            if profile.bg_id is None:
                request.session['account_id'] = user.account_id
                request.session['profile_id'] = profile.df_id
                messages.info(request, 'Please complete your background information to continue.')
                return redirect('create_profile_step')
            return redirect('profile_detail')

        except Profile.DoesNotExist:
            request.session['account_id'] = user.account_id
            messages.info(request, 'Your account is not yet linked to a profile. Please complete your personal information.')
            return redirect('create_profile')


    if request.method == 'POST':
        form = CustomAuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if not user.is_active:
                    messages.success(request, 'Your account is deactivated, please contact admin to reactivate it to use it again')
                    return redirect('index')

                if not user.is_verified:
                    messages.success(request, 'Please wait for the verification of the officers.')
                    return redirect('index')
                
                # if user.is_verified or (user.last_login_date and (timezone.now() - user.last_login_date).days > 30):
                #     otp = user.generate_otp()

                #     # Get current domain, e.g. '127.0.0.1:8000' or 'yourdomain.com'
                #     domain = get_current_site(request).domain
                    
                #     # Render email with absolute image path
                #     html_message = render_to_string('components/otp_email.html', {
                #         'otp': otp,
                #         'domain': domain  # Pass domain to template
                #     })
                #     plain_message = strip_tags(html_message)
                #     from_email = 'gensanity.information@gmail.com'
                #     to = user.email

                #     send_mail(
                #         'Your OTP Code',
                #         plain_message,
                #         from_email,
                #         [to],
                #         html_message=html_message,
                #         fail_silently=False,
                #     )

                #     messages.info(request, 'OTP sent to your email.')
                #     return render(request, 'login.html', {'user_id': user.account_id, 'form': form})

                login(request, user)
                user.last_login_date = timezone.now()
                user.save()

                try:
                    if user.is_staff:
                        return redirect(reverse('admin:index'))
                    profile = Profile.objects.get(account_id=user)
                    if profile.bg_id is None:
                        request.session['account_id'] = user.account_id
                        request.session['profile_id'] = profile.df_id
                        messages.warning(request, 'Error L100 - Account has no Background information.')
                        return redirect('create_profile_step')
                    else:
                        return redirect('profile_detail')

                except Profile.DoesNotExist:
                    request.session['account_id'] = user.account_id
                    messages.warning(request, 'Error L200 - Account has no Profile information.')
                    return redirect('create_profile')

                messages.success(request, 'Logged in successfully.')
            else:
                if Account.objects.filter(username=username).exists():
                    messages.error(request, 'Incorrect password. Please try again.')
                else:
                    messages.error(request, 'Invalid username or password.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error L400 - {error} or your account might be deactivated, please contact the Admin for reactivation.")
    else:
        form = CustomAuthenticationForm()

    return render(request, 'login.html', {'form': form})


@login_required
def activate_account(request, account_id):
    account = get_object_or_404(Account, pk=account_id)
    account.is_active = True
    account.save()
    return redirect('account_detail', account_id=account_id)  # Redirect to a page showing account details

@login_required
def account_status(request, account_id):
    account = get_object_or_404(Account, pk=account_id)
    return render(request, 'inactive.html', {'account': account})

# Populate the Address Selection 
def get_provinces(request):
    region_id = request.GET.get('region_id')
    provinces = Province.objects.filter(region_id=region_id).values('province_id', 'province')
    return JsonResponse({'provinces': list(provinces)})

def get_skills(request):
    # Assuming you have a Skill model with id and name fields
    skills = Skills.objects.all().values('skill_id', 'skill')
    return JsonResponse({'skills': list(skills)})
def get_languages(request):
    # Assuming you have a Language model with id and name fields
    languages = Language.objects.all().values('language_id', 'language')
    return JsonResponse({'languages': list(languages)})


def get_cities(request):
    province_id = request.GET.get('province_id')
    cities = City.objects.filter(province_id=province_id).values('city_id', 'city')
    return JsonResponse({'cities': list(cities)})

def get_barangays(request):
    city_id = request.GET.get('city_id')
    barangays = Barangay.objects.filter(city_id=city_id).values('barangay_id', 'barangay')
    return JsonResponse({'barangays': list(barangays)})

def create_account(request):
    step_number = 1
    if request.method == 'POST':
        form = AccountForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']

            # Check if an account with the same username or email already exists
            if Account.objects.filter(username=username).exists() or Account.objects.filter(email=email).exists():
                messages.error(request, 'R100 - Sorry, that username or email address already exists.')
            else:
                # Store form data in session
                latest_account_id = Account.objects.aggregate(max_id=Max('account_id'))['max_id'] or 0
                new_account_id = latest_account_id + 1

                request.session['username'] = username
                request.session['email'] = email
                request.session['password'] = password
                request.session['account_id'] = new_account_id  # Store the new account_id in session

                # Add a success message for the next step
                messages.success(request, 'Account information saved. Proceed to finish your registration.')
                
                # Redirect to a finishing step or confirmation page
                return redirect('create_profile')
        else:
            # Form is invalid, add error messages for each field
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error in {field}: {error}')
    else:
        form = AccountForm()
        step_number = 1

    # Include step_number in the context dictionary
    context = {'form': form, 'step_number': step_number}

    return render(request, 'components/signup-form-1.html', context)

import base64
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import IntegrityError

def finish_registration(request):
    step_number = 4
    profile_data = request.session.get('profile_data')
    background = request.session.get('background')

    if request.method == 'POST':
        username = request.session.get('username')
        email = request.session.get('email')
        password = request.session.get('password')
        account_id = request.session.get('account_id')
        from datetime import datetime

        if username and email and password and profile_data:
            with transaction.atomic():
                # Save account
                
                try:
                    account, created = Account.objects.get_or_create(account_id=account_id, username=username, email=email)
                    if created:
                        account.set_password(password)
                        account.save()
                    else:
                        pass
                except IntegrityError as e:
                    messages.error(request, f"Error creating account: {e}")
                # Decode and prepare the picture file
                date_of_birth = profile_data.get('date_of_birth')
                if date_of_birth:
                    try:
                        # Parse the date if it is not in 'YYYY-MM-DD' format
                        date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
                    except ValueError:
                        # If only the year is provided (e.g., '2024'), default to January 1st of that year
                        try:
                            date_of_birth = datetime.strptime(date_of_birth, "%Y").date().replace(month=1, day=1)
                        except ValueError:
                            date_of_birth = None  # Handle as needed, e.g., default to today's date or raise an error
                profile = Profile(
                    account_id=account,
                    first_name=profile_data.get('first_name'),
                    last_name=profile_data.get('last_name'),
                    suffix=profile_data.get('suffix'),
                    middle_name=profile_data.get('middle_name'),
                    region_id=profile_data.get('region'),
                    province_id=profile_data.get('province'),
                    city_id=profile_data.get('city'),
                    barangay_id=profile_data.get('barangay'),
                    zip=profile_data.get('zip'),
                    house_no=profile_data.get('house_no'),
                    street=profile_data.get('street'),
                    date_of_birth=profile_data.get('date_of_birth'),
                    contact_no=profile_data.get('contact_no'),
                    gender=profile_data.get('gender'),
                    qoute=profile_data.get('qoute'),
                    pronoun=profile_data.get('pronoun'),
                    is_pwd=profile_data.get('is_pwd'),
                    is_4ps=profile_data.get('is_4ps')
                )

                # Handle base64 picture data if present
                picture_data = profile_data.get('picture')
                # Handle base64 picture data if present
                if picture_data:
                    try:
                        # Check if the data starts with 'data:image/jpeg;base64,' or similar
                        if ';base64,' in picture_data:
                            format, imgstr = picture_data.split(';base64,')
                        else:
                            # Prepend default format if missing
                            imgstr = picture_data
                            format = 'data:image/jpeg'  # Adjust based on expected format

                        ext = format.split('/')[-1]  # Get the file extension
                        img_data = ContentFile(base64.b64decode(imgstr), name=f"{username}_profile.{ext}")

                        # Save the image to the profile
                        profile.picture.save(img_data.name, img_data, save=False)

                    except Exception as e:
                        messages.error(request, f"Error decoding picture data: {e}")
                
                
                profile.save()  # Save the profile first


                # Retrieve or create resume and link to profile
                resume_id = request.session.get('resume_id')
                if resume_id:
                    resume, created = Resume.objects.get_or_create(id=resume_id, defaults={'profile': profile})
                    if not created:
                        resume.profile = profile  # Update the profile if it already exists
                        resume.save()

                # Retrieve or create projects and link to profile
                for project_id in request.session.get('project_ids', []):
                    project, created = Project.objects.get_or_create(id=project_id, defaults={'profile': profile})
                    if not created:
                        project.profile = profile  # Update profile if it already exists
                        project.save()
               
                # Save background information
                if background:
                    background_info = BackgroundInformation(
                        profile=profile,
                        affiliation_id=background['background_data'].get('affiliation_id'),
                        specialization_id=background['background_data'].get('specialization_id')
                    )
                    background_info.save()

                    profile.bg_id = background_info
                    profile.save()

                    # Save languages with proficiency levels
                    for language_id in background['background_data'].get('languages_ids', []):
                        BackgroundInformationLanguage.objects.create(
                            background_information=background_info,
                            language_id=language_id,
                            proficiency_level='basic'  # Adjust proficiency level as needed
                        )

                    # Set skills for background information
                    skill_ids = background['background_data'].get('skills_ids', [])
                    background_info.skills.set(skill_ids)

                # Process past experiences
                 # Handle past experiences
                background_info_data = request.session.get('background', {})
                past_experience_data_list = background_info_data.get('past_experiences_data', [])
                if past_experience_data_list:  # Check if the list is not empty
                    for past_experience_data in past_experience_data_list:
                        if (past_experience_data.get('client') is not None and past_experience_data.get('country') is not None and past_experience_data.get('year') is not None):                            # Assuming past_experience_data is a dict-like structure
                            year = past_experience_data.get('year')
                            year_date = None
                            if year:
                                try:
                                    # Attempt to parse 'year' as 'YYYY-MM-DD'
                                    year_date = datetime.strptime(year, "%Y-%m-%d").date()
                                except ValueError:
                                    # If only 'YYYY' is provided, set it to January 1st of that year
                                    try:
                                        year_date = datetime.strptime(year, "%Y").date().replace(month=1, day=1)
                                    except ValueError:
                                        year_date = None  # Handle this as needed, e.g., set a default

                            # Update the past_experience_data with the formatted year
                            if year_date:
                                past_experience_data['year'] = year_date

                            # Create and save the PastExperience instance
                            past_experience = PastExperience(**past_experience_data)
                            past_experience.save()
                

                            # Print the added past experience details

                            # Connect the saved PastExperience with BackgroundInformation
                            background_info.past_experiences.add(past_experience)
                
                # Clear session data
                for key in ['username', 'email', 'password', 'profile_data', 'resume_id', 'background', 'project_ids']:
                    if key in request.session:
                        del request.session[key]

                messages.success(request, 'Congratulations, your profile and account have been successfully created. Please for the Administrator to validate your Account. It will take 1-5 business days.')
                return redirect('user_login')

        else:
            messages.error(request, 'Some data is missing. Please try again.')

    context = {'step_number': step_number}
    return render(request, 'components/finish_registration.html', context)

def create_profile(request):
    step_number = 2

    # Retrieve account information from session
    account_id = request.session.get('account_id')

    if not account_id:
        messages.error(request, 'Account information is missing. Please create an account first.')
        return redirect('user_login')

    latest_profile_id = Profile.objects.aggregate(Max('df_id'))['df_id__max'] or 0
    new_profile_id = latest_profile_id + 1

    # Check if an existing profile with the given account_id exists
    existing_profile = Profile.objects.filter(account_id=account_id).first()
    if existing_profile:
        messages.error(request, 'Profile with the provided account_id already exists.')
        return redirect('user_login')

    if request.method == 'POST':
        # Include account_id in the form data
        request.POST = request.POST.copy()
        request.POST['account_id'] = account_id
        request.POST['df_id'] = new_profile_id

        request.POST['qoute'] = 'Having people acknowledge your existence is a wonderful thing.'

        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            # Get cleaned data from the form and convert any non-serializable objects
            profile_data = form.cleaned_data
            
            # Convert Region and other model fields to their IDs or other serializable formats
            if 'region' in profile_data and profile_data['region']:
                profile_data['region'] = profile_data['region'].region_id
            if 'province' in profile_data and profile_data['province']:
                profile_data['province'] = profile_data['province'].province_id
            if 'city' in profile_data and profile_data['city']:
                profile_data['city'] = profile_data['city'].city_id
            if 'barangay' in profile_data and profile_data['barangay']:
                profile_data['barangay'] = profile_data['barangay'].barangay_id
            if 'date_of_birth' in profile_data and profile_data['date_of_birth']:
                profile_data['date_of_birth'] = profile_data['date_of_birth'].isoformat()
            # Store profile data in session

             # Remove file fields before saving to session
           # Handle image separately
            if 'picture' in request.FILES:
                image_file = request.FILES['picture']
                image_content = base64.b64encode(image_file.read()).decode('utf-8')
                profile_data['picture'] = image_content
            max_df_id = Profile.objects.aggregate(Max('df_id'))['df_id__max']
            initial_df_id = (max_df_id + 1) if max_df_id is not None else 1

            # Store profile data in session
            request.session['profile_data'] = profile_data
            request.session['df_id'] = initial_df_id

            # Add a success message
            messages.success(request, 'Profile information saved temporarily. Please confirm to complete.')
            
            # Redirect to a confirmation page or another step
            return redirect('create_profile_step')  # Make sure to create this view


        else:
            messages.error(request, 'Failed to create the profile. Please check the form for errors.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        # Set the initial value for the form
        form = ProfileForm(initial={'account_id': account_id})

    # Include step_number and account_id in the context dictionary
    context = {'form': form, 'step_number': step_number, 'account_id': account_id}

    return render(request, 'components/create-profile-form.html', context)


def handle_formset_errors(request, project_formset, resume_form, background_form, past_experience_formset):
    """Helper function to process errors for formsets."""
    if not project_formset.is_valid():
        messages.error(request, 'There are errors in the project section. Please review the fields.')
        for form in project_formset:
            if form.errors:
                for field, error in form.errors.items():
                    messages.error(request, f"Project form error in '{field}': {', '.join(error)}")

    if not resume_form.is_valid():
        messages.error(request, 'There are errors in the resume section. Please review the fields.')
        for field, error in resume_form.errors.items():
            messages.error(request, f"Resume form error in '{field}': {', '.join(error)}")

    if not background_form.is_valid():
        messages.error(request, 'There are errors in the background information section. Please review the fields.')
        for field, error in background_form.errors.items():
            messages.error(request, f"Background form error in '{field}': {', '.join(error)}")

    if not past_experience_formset.is_valid():
        messages.error(request, 'There are errors in the past experience section. Please review the fields.')
        for form in past_experience_formset:
            if form.errors:
                for field, error in form.errors.items():
                    messages.error(request, f"Past experience form error in '{field}': {', '.join(error)}")



def create_profile_step(request):
    template_name = 'components/create-profile-step.html'
    step_number = 3  # This is the third step in profile creation

    # Get profile ID from the session
    df_id = request.session.get('df_id')
    if not df_id:
        messages.error(request, 'Profile information is missing. Please create an account first.')
        return redirect('user_login')

    if request.method == 'POST':
    
        with transaction.atomic():
            post_data = request.POST.copy()
            titles = post_data.getlist('title')
            descriptions = post_data.getlist('description')
            
            for index, (title, description) in enumerate(zip(titles, descriptions)):
                post_data[f'projects-{index}-title'] = title
                post_data[f'projects-{index}-description'] = description
                # Include the corresponding pdf_file for each project
                if index < len(request.FILES.getlist('projects-0-pdf_file')):
                    post_data[f'projects-{index}-pdf_file'] = request.FILES.getlist('projects-0-pdf_file')[index]
             # Set the total number of forms in the formset
            post_data['projects-TOTAL_FORMS'] = len(titles)
            post_data['projects-INITIAL_FORMS'] = 0  # Initial forms count is 0 as this is for new entries
            
            project_formset = ProjectFormSet(post_data, request.FILES, prefix='projects')
            resume_form = ResumeForm(request.POST, request.FILES)
            background_form = BackgroundInformationForm(request.POST)
            past_experience_formset = PastExperienceFormSet(request.POST, prefix='past_experience')
            if (project_formset.is_valid() and resume_form.is_valid() 
                    and background_form.is_valid() and past_experience_formset.is_valid()):
                
                # Fetch the profile instance using df_id
                # Save resume file to database
                resume_file = resume_form.cleaned_data.get('resume_file')
                if resume_file:
                    resume = Resume.objects.create(resume_file=resume_file)
                    request.session['resume_id'] = resume.id  # Store resume ID in session

                # Save project files and details to the database
                project_ids = []
                for form in project_formset:
                    if form.is_valid():
                        project_data = form.cleaned_data
                        project = Project.objects.create(
                            title=project_data.get('title'),
                            description=project_data.get('description'),
                            pdf_file=project_data.get('pdf_file')
                        )
                        project_ids.append(project.id)  # Add project ID to the list

                # Store the list of project IDs in the session
                request.session['project_ids'] = project_ids

                # Store non-file data in the session if needed
                background_data = {
                    'affiliation_id': background_form.cleaned_data.get('affiliation').aff_id if background_form.cleaned_data.get('affiliation') else None,
                    'specialization_id': background_form.cleaned_data.get('specialization').specialization_id if background_form.cleaned_data.get('specialization') else None,
                    'languages_ids': [language.language_id for language in background_form.cleaned_data.get('languages', [])],
                    'skills_ids': [skill.skill_id for skill in background_form.cleaned_data.get('skills', [])],
                }

                # Save background data and past experiences to session for further processing
                request.session['background'] = {
                    'background_data': background_data,
                    'past_experiences_data': [
                        {
                            'client': form.cleaned_data.get('client'), 
                            'country_id': form.cleaned_data.get('country').country_id if form.cleaned_data.get('country') else None, 
                            'year': form.cleaned_data.get('year').strftime('%Y') if form.cleaned_data.get('year') else None  # Convert date to string
                        }
                        for form in past_experience_formset if form.is_valid()
                    ],
                }

                
                messages.success(request, 'Profile information saved temporarily. Proceed to finalize registration.')

                # Redirect to `finish_registration` for final saving
                return redirect('finish_registration')
            else:
                handle_formset_errors(request, project_formset, resume_form, background_form, past_experience_formset)
    else:
        project_formset = ProjectFormSet(queryset=Project.objects.none(), prefix='projects')
        resume_form = ResumeForm()
        background_form = BackgroundInformationForm(initial={'df_id': df_id})
        past_experience_formset = PastExperienceFormSet(prefix='past_experience')

    context = {
        'project_formset': project_formset,
        'resume_form': resume_form,
        'background_form': background_form,
        'past_experience_formset': past_experience_formset,
        'step_number': step_number,
        'df_id': df_id,
    }

    return render(request, template_name, context)


def get_all_countries(request):
    countries = Country.objects.values('country_id', 'country')
    return JsonResponse({'countries': list(countries)})

def get_notifications(user):
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    unread_notifications = Notification.objects.filter(
        user=user, 
        is_read=False, 
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')
    
    read_notifications = Notification.objects.filter(
        user=user, 
        is_read=True, 
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')
    
    return unread_notifications, read_notifications

@login_required
def notification_page(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    account_id = request.user.account_id
    # Fetch unread and read notifications for the current user
    unread_notifications, read_notifications = get_notifications(account_id)


    context = {
        'notifications_unread': unread_notifications,
        'notifications_read': read_notifications,
        'profile':user_profile,
    }

    return render(request, 'freelancer/notification_page.html', context)

@login_required(login_url='user_login')
def profile_detail(request):
    account_id = request.user.account_id
    try:
        user_profile = Profile.objects.get(account_id=account_id)

    except Profile.DoesNotExist:
        try:
            account = Account.objects.get(account_id=account_id)
            request.session['username'] = account.username
            request.session['email'] = account.email
            request.session['password'] = account.password
            request.session['account_id'] = account.account_id
            messages.info(
                request,
                "Your account is not yet linked to a complete profile. Please provide your personal information to continue. If you believe this is a mistake, kindly contact the administrator."
            )
        except Account.DoesNotExist:
            messages.error(request, 'Account does not exist.')
            return redirect('index')

        return redirect('create_profile')

    if not request.user.is_verified:
        messages.info(request, 'Your account is pending verification by the admin. Please wait.')
        return redirect('index')

    
    current_date = date.today()
    next_week = current_date + timedelta(days=7)
    tomorrow_date = current_date + timedelta(days=1)
    one_week_from_now = current_date + timedelta(days=7)
    background_info = user_profile.bg_id
    
    if background_info:
        # Get all the skill IDs associated with the user's background information
        user_skill_ids = background_info.skills.values_list('skill_id', flat=True)
        # Get all the tags associated with these skills
        tag_ids = Tag.objects.filter(skills__skill_id__in=user_skill_ids).values_list('id', flat=True)

        # Filter announcements using these tags
        announcements_foryou = Announcement.objects.filter(
            tags__in=tag_ids
        ).order_by('-created_at')
        
        # If no announcements are found, fallback to the latest 3 announcements
        if not announcements_foryou.exists():
            announcements_foryou = Announcement.objects.all().order_by('-created_at')[:3]
    else:
        # If no background_info, get the latest 3 announcements
        announcements_foryou = Announcement.objects.all().order_by('-created_at')[:3]

    all_events = Event.objects.all()
    # Filter events to only include published events with tags "General" or "Public"
    events = Event.objects.filter(
        is_published=True,
        start_datetime__date__gte=current_date,
    ).order_by('start_datetime')

    # Separate current day's events and next week's events
    current_day_events = events.filter(
        start_datetime__date__lte=current_date,
        end_datetime__date__gte=current_date
    )[:5]    
    tomorrow_events = events.filter(start_datetime__date=tomorrow_date)[:5]
    next_week_events = events.filter(start_datetime__date__gt=current_date, start_datetime__date__lte=one_week_from_now)[:5]
    future_events = events.filter(start_datetime__date__gte=current_date)
    
    # Separate events into upcoming, attended, and previous categories
    upcoming_events = future_events[:5]
    attended_events = Attendance.objects.filter(user=request.user).values_list('event', flat=True)[:5]
    previous_events = Event.objects.filter(start_datetime__date__lt=current_date)[:5]

    # Get RSVP status for upcoming events
    upcoming_events_with_rsvp = []
    for event in upcoming_events:
        rsvp = RSVP.objects.filter(user=request.user, event=event).first()
        event.rsvp_status = rsvp.status if rsvp else None
        upcoming_events_with_rsvp.append(event)


    projects = Project.objects.filter(profile=user_profile)

    # Get unread notifications
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    context = {
        'profile': user_profile,
        'current_date': current_date,
        'current_day_events': current_day_events,
        'tomorrow_events': tomorrow_events,
        'future_events': future_events,
        'next_week_events': next_week_events,
        'projects': projects,
        'announcements': announcements_foryou,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
        'upcoming_events': upcoming_events_with_rsvp,  # Updated to pass upcoming events with RSVP
        'attended_events': all_events.filter(id__in=attended_events),  # Filter attended events
        'previous_events': previous_events,  # Filter previous events
    }
    return render(request, 'freelancer/profile_detail.html', context)


@login_required(login_url='user_login')
def profile_page(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    certificates = Certificate.objects.filter(profile=user_profile)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    attended_events = Event.objects.filter(attendances__user=request.user).order_by('-start_datetime')[:10]
    background_info = get_object_or_404(BackgroundInformation, bg_id=user_profile.bg_id_id)
    projects = Project.objects.filter(profile=user_profile)
    resumes = Resume.objects.filter(profile=user_profile)
    resume_count = resumes.count()
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    skills = background_info.skills.all()
    languages = background_info.language.all()
    past_experiences = background_info.past_experiences.order_by('year').all()
    project_form = ProjectForm(request.POST or None, request.FILES or None)
    resume_form = ResumeForm(request.POST or None, request.FILES or None)
    language_form = LanguageForm(request.POST or None)
    skills_form = SkillsForm(request.POST or None)
    past_experience_form = PastExperienceForm(request.POST or None)
    certificate_form = CertificateForm(request.POST or None, request.FILES or None)
    # Filter events to only include published events with tags "General" or "Public"
    
    current_date = date.today()
    next_week = current_date + timedelta(days=7)
    tomorrow_date = current_date + timedelta(days=1)
    one_week_from_now = current_date + timedelta(days=7)
    # Separate current day's events and next week's events
    events = Event.objects.filter(
        is_published=True,
        start_datetime__date__gte=current_date,
    ).order_by('start_datetime')

    current_day_events = events.filter(start_datetime__date=current_date)
    tomorrow_events = events.filter(start_datetime__date=tomorrow_date)
    next_week_events = events.filter(start_datetime__date__gt=current_date, start_datetime__date__lte=one_week_from_now)
    future_events = events.filter(start_datetime__date__gt=current_date)

    # Separate events into upcoming, attended, and previous categories
    upcoming_events = future_events
    attended_events = Attendance.objects.filter(user=request.user, logged_in=True).values_list('event', flat=True)
    previous_events = Event.objects.filter(start_datetime__date__lt=current_date)

    if request.method == 'POST':
        if 'certificate_submit' in request.POST:
            resume_form = None
            skills_form = None
            language_form = None
            past_experience_form = None
            if certificate_form.is_valid():
                certificate = certificate_form.save(commit=False)
                certificate.profile = user_profile
                certificate.save()
                return redirect('profile_page')
            else:
                messages.error(request, 'Certificate Submssion Failed')
        elif 'remove_certificate' in request.POST:
            certificate_id = request.POST.get('remove_project')
            certificate_to_remove = Certificate.objects.get(id=certificate_id)
            certificate_to_remove.delete()
            messages.success(request, 'Certificate Removed Successfully')
        
        elif 'project_submit' in request.POST:
            resume_form = None
            skills_form = None
            language_form = None
            past_experience_form = None
            certificate_form = None
            if project_form.is_valid():
                project = project_form.save(commit=False)
                project.profile = user_profile
                project.save()
                project_form = ProjectForm()  # Clear the form after saving
                messages.success(request, 'Project Submission Succesful')
                return redirect('profile_page')
            else:
                messages.error(request, 'Project Submssion Failed')

        elif 'resume_submit' in request.POST:
            project_form = None
            skills_form = None
            language_form = None
            past_experience_form = None
            certificate_form = None
            if resume_form.is_valid():
                resume = resume_form.save(commit=False)
                resume.profile = user_profile
                resume.save()
                messages.success(request, 'Resume Submission Success')
                return redirect('profile_page')
            else:
                messages.error(request, 'Resume Submission Failed')
            
        elif 'language_submit' in request.POST:
            resume_form = None
            project_form = None
            skills_form = None
            past_experience_form = None
            certificate_form = None
            if language_form.is_valid():
                language = language_form.cleaned_data.get('language')
                for language_obj in language:
                    background_info.language.add(language_obj)
                background_info.save()
                messages.success(request, 'New Language Added Successfully')
                return redirect('profile_page')
            else:
                for field, errors in language_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in field '{field}': {error}")
                
        elif 'skills_submit' in request.POST:
            resume_form = None
            project_form = None
            language_form = None
            past_experience_form = None
            certificate_form = None
            if skills_form.is_valid():
                skill = skills_form.cleaned_data.get('skills') 
                for skill_obj in skill:
                    background_info.skills.add(skill_obj)
                background_info.save()
                messages.success(request, 'New Skill Added')
                return redirect('profile_page')
            else:
               for field, errors in skills_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in field '{field}': {error}")
                

        elif 'remove_language' in request.POST:
            language_id = request.POST.get('remove_language')
            language_to_remove = Language.objects.get(language_id=language_id)
            background_info.language.remove(language_to_remove)
            messages.success(request, 'Language Removed Successfully')

        elif 'remove_skill' in request.POST:
            skill_id = request.POST.get('remove_skill')
            skill_to_remove = Skills.objects.get(skill_id=skill_id)
            background_info.skills.remove(skill_to_remove)
            messages.success(request, 'Skill Removed Successfully')

        elif 'remove_project' in request.POST:
            project_id = request.POST.get('remove_project')
            project_to_remove = Project.objects.get(id=project_id)
            project_to_remove.delete()
            messages.success(request, 'Project Removed Successfully')
        
        elif 'remove_resume' in request.POST:
            resume_id = request.POST.get('remove_resume')
            resume_to_remove = Resume.objects.get(id=resume_id)
            resume_to_remove.delete()
            messages.success(request, 'Resume Removed Successfully')

        elif 'remove_past_experience' in request.POST:
            past_exp_id = request.POST.get('remove_past_experience')
            try:
                # Retrieve and remove the experience
                past_experience = get_object_or_404(PastExperience, past_exp_id=past_exp_id, backgroundinformation=user_profile.bg_id)
                background_info.past_experiences.remove(past_experience)
                past_experience.delete()
                background_info.save()
                messages.success(request, 'Past Experience Removed Successfully')
                return redirect('profile_page')
            except PastExperience.DoesNotExist:
                messages.error(request, 'Past Experience Not Found')

        elif 'past_exp_submit' in request.POST:
            resume_form = None
            project_form = None
            language_form = None
            skills_form = None
            certificate_form = None
            if past_experience_form.is_valid():
                past_experience = past_experience_form.save(commit=False)
                past_experience.profile = user_profile
                past_experience.save()
                background_info.past_experiences.add(past_experience)
                background_info.save()
                messages.success(request, 'Past Experience Submitted Succesfully')
                return redirect('profile_page')
            else:
                messages.error(request, 'Past Experience Submission Error')
                
    context = {
        'profile': user_profile, 
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
        'projects': projects,
        'skills': skills,
        'languages': languages,
        'resumes': resumes,
        'past_experiences':past_experiences,
        'project_form': project_form,
        'resume_form': resume_form,
        'language_form': language_form,
        'skills_form': skills_form,
        'resume_count': resume_count,
        'past_experience_form': past_experience_form,
        'attended_events': events.filter(id__in=attended_events),  # Filter attended events
        'previous_events': previous_events,  # Filter previous events
        'certificates': certificates,
        'certificate_form': certificate_form,
        }
    
    return render(request, 'freelancer/profile_page.html', context)

@login_required(login_url='user_login')
def add_project(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.profile = user_profile
            project.save()
            messages.success(request, 'Your project has been added successfully!')
            return redirect('profile_page')  # Redirect to home page after successful submission
        else:
            messages.error(request, 'There was an error with your submission. Please correct the errors and try again.')
    else:
        form = ProjectForm()
    
    return render(request, 'freelancer/modals/add_project.html', {'project_form': form, 'profile': user_profile, 'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,})

@login_required(login_url='user_login')
def update_project(request, project_id):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    # Get the project based on its ID
    project = get_object_or_404(Project, id=project_id)
    
    # Ensure that only the project owner can update the project
    if request.user != project.profile.account_id:
        messages.error(request, "You don't have permission to edit this project.")
        return redirect('profile_page')  # Redirect to profile if the user is not the owner

    if request.method == 'POST':
        # Update project with form data
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('profile_page')  # Redirect to profile page after a successful update
        else:
            messages.error(request, 'There was an error with your submission. Please correct the errors and try again.')
    else:
        # Prepopulate the form with existing project data
        form = ProjectForm(instance=project)
    
    # Render the update form
    return render(request, 'freelancer/modals/update_project.html', {'project_form': form, 'project': project, 'profile': user_profile, 'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,})

@login_required(login_url='user_login')
def edit_profile(request, account_id):
    profile = get_object_or_404(Profile, account_id=account_id)
    form = UpdateProfileForm(instance=profile)
    bgform = UpdateBackgroundInformationForm(instance=profile.bg_id)
    notifications_unread, notifications_read = get_notifications(profile.account_id.account_id)
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, request.FILES, instance=profile)
        bgform = UpdateBackgroundInformationForm(request.POST, request.FILES, instance=profile.bg_id)
        if 'edit_profile' in request.POST:
            bgform = None

            # Get the profile instance related to the current user
            profile = profile

            # Initialize the form with POST data and instance of the profile
            fields = [
                'first_name', 'last_name', 'suffix', 'middle_name',
                'region', 'province', 'city', 'barangay',
                'zip', 'house_no', 'street',
                'date_of_birth', 'contact_no', 'gender', 'picture', 'account_id', 'qoute'
            ]

            # Loop through each field and use existing profile data if form data is None
            for field in fields:
                if getattr(profile, field) is None:
                    setattr(profile, field, getattr(profile, field, None))

            if form.is_valid():
                profile = form.save(commit=False)
                 # Fields to check and populate with existing data if None
               
                # Ensure the account_id is set if profile has an account
                if hasattr(profile, 'account') and profile.account is not None:
                    profile.account_id = profile.account.account_id

                profile.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('profile_page')
            else:
                messages.error(request, 'Profile information update failed. Please correct the errors below.')
        elif 'edit_bg' in request.POST:
            form = None
            if bgform.is_valid():
                bgform.save()
                messages.success(request, 'Background information updated successfully.')
                return redirect('profile_page')
            else:
                messages.error(request, 'Background information update failed. Please correct the errors below.')

    return render(request, 'freelancer/edit_profile.html', {'form': form, 'bgform':bgform, 'profile':profile, 'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,})


@login_required(login_url='user_login')
def announcement_view(request):
    active_tab = 1
    user_profile = get_object_or_404(Profile, account_id=request.user)
    current_date = date.today()

    background_info = user_profile.bg_id
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    all_tags = Tag.objects.all()
    query = request.GET.get('q', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_tag_ids = request.GET.getlist('tag')
    sort = request.GET.get('sort')

    # Start with all announcements
    all_announcements = Announcement.objects.all()
    announcements_foryou = Announcement.objects.none()

    # Filter by background skills → tags
    if background_info:
        user_skill_ids = background_info.skills.values_list('skill_id', flat=True)
        user_tag_ids = Tag.objects.filter(skills__skill_id__in=user_skill_ids).values_list('id', flat=True)
        announcements_foryou = Announcement.objects.filter(tags__in=user_tag_ids).distinct()

    # Apply filters (search, date, tags)
    if query:
        search_filter = Q(title__icontains=query) | Q(content__icontains=query)
        all_announcements = all_announcements.filter(search_filter)
        announcements_foryou = announcements_foryou.filter(search_filter)

    if start_date and end_date:
        date_filter = Q(created_at__date__range=[start_date, end_date])
        all_announcements = all_announcements.filter(date_filter)
        announcements_foryou = announcements_foryou.filter(date_filter)

    if selected_tag_ids:
        all_announcements = all_announcements.filter(tags__id__in=selected_tag_ids)
        announcements_foryou = announcements_foryou.filter(tags__id__in=selected_tag_ids)

    # Sort
    if sort == 'latest':
        all_announcements = all_announcements.order_by('-created_at')
        announcements_foryou = announcements_foryou.order_by('-created_at')
    elif sort == 'oldest':
        all_announcements = all_announcements.order_by('created_at')
        announcements_foryou = announcements_foryou.order_by('created_at')
    elif sort == 'relevant' and background_info:
        announcements_foryou = announcements_foryou.order_by('-created_at')
        all_announcements = all_announcements.none()

    # Pagination
    paginator = Paginator(all_announcements, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': user_profile,
        'announcements_foryou': announcements_foryou,
        'page_obj': page_obj,
        'current_date': current_date,
        'all_tags': all_tags,
        'selected_tag_ids': selected_tag_ids,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
        'active_tab': active_tab,
        'sort': sort,
    }

    return render(request, 'freelancer/announcement.html', context)


@login_required(login_url='user_login')
def logout_view(request):
    # Add a logout message
    messages.success(request, 'Logged out successfully.')

    logout(request)

    # Redirect to a specific page after logout
    return redirect('index')  # Replace 'index' with the desired URL name or path

@login_required(login_url='user_login')
def update_projects_view(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    project_form = ProjectForm(request.POST or None, request.FILES or None)
    projects = Project.objects.filter(profile=user_profile)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    if 'project_submit' in request.POST:
        if project_form.is_valid():
            project = project_form.save(commit=False)
            project.profile = user_profile
            project.save()
            project_form = ProjectForm()  # Clear the form after saving
            messages.success(request, 'Project Submission Succesful')
            redirect 
        else:
            messages.error(request, 'Project Submssion Failed')

    if request.method == 'POST':
        # Handle delete requests
        for project in projects:
            if f'delete_{project.id}' in request.POST:
                project.delete()
                messages.success(request, f'Project "{project.title}" deleted successfully.')
                return redirect('profile_page')  # Redirect immediately after deletion to avoid further processing

        # Handle update requests
        for project in projects:
            form = ProjectForm(request.POST, request.FILES, instance=project, prefix=f'project_{project.id}')
            if form.is_valid():
                form.save()
                messages.success(request, f'Project "{project.title}" updated successfully.')
            else:
                # Add detailed form error messages
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in project '{project.title}', field '{field}': {error}")
                                # Generic error message

        return redirect('profile_page')

    else:
        # Create a dictionary of forms keyed by project ID
        forms = {project.id: ProjectForm(instance=project, prefix=f'project_{project.id}') for project in projects}

    context = {
        'forms': forms,
        'project_form': project_form,
        'projects': projects,
        'profile': user_profile,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }

    return render(request, 'freelancer/update_project.html', context)



@login_required(login_url='user_login')
def update_resume_view(request, resume_id, account_id):
    user_profile = get_object_or_404(Profile, account_id=account_id)
    resume = get_object_or_404(Resume, id=resume_id)
    resumes = Resume.objects.filter(profile=user_profile)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    if request.method == 'POST':
        if 'delete' in request.POST:
            resume.delete()
            return redirect('profile_page')  # Redirect to the portfolio view after deleting
        else:
            form = ResumeForm(request.POST, request.FILES, instance=resume)
            if form.is_valid():
                form.save()
                messages.success(request, 'Resume Updated Succesfully')
                return redirect('profile_page')  # Redirect to the portfolio view after 
            else:
                messages.error(request, 'Resume Update Failed')
    else:
        form = ResumeForm(instance=resume)

    return render(request, 'freelancer/update_resume.html', {'form': form, 'resume': resume, 'profile': user_profile, 'resumes': resumes,  'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,})

@login_required(login_url='user_login')
def update_account(request):
    user = request.user  # Assuming the user is authenticated
    user_profile = get_object_or_404(Profile, account_id=request.user)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    
    if request.method == 'POST':
        if 'change_password' in request.POST:
            form = PasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                # Add a success message
                messages.success(request, 'Password updated successfully.')
                # Redirect to the settings page
                return redirect('settings')
        elif 'deactivate_account' in request.POST:
            user.is_active = False
            user.save()
            # Add a success message
            messages.success(request, 'Account deactivated successfully.')
            # Log the user out
            logout(request)
            # Redirect to the login page
            return redirect('user_login')
    else:
        form = PasswordChangeForm(user)

    # Include form and profile in the context dictionary
    context = {
        'form': form, 
        'profile': user_profile, 
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }

    return render(request, 'freelancer/settings.html', context)

@login_required(login_url='user_login')
def event_view(request):
    active_tab = 2
    user_profile = get_object_or_404(Profile, account_id=request.user)
    current_date = date.today()
    one_week_later = current_date + timedelta(weeks=1)

    # Filters from request
    search_query = request.GET.get('search', '')
    tag_filter = request.GET.get('tag', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    filter_choice = request.GET.get('filter_choice', 'active')
    sort = request.GET.get('sort')

    # Get freelancer skill tags
    try:
        background_info = BackgroundInformation.objects.get(profile=user_profile)
        freelancer_skills = background_info.skills.prefetch_related('tags')
    except BackgroundInformation.DoesNotExist:
        freelancer_skills = Skills.objects.none()

    skill_ids = freelancer_skills.values_list('skill_id', flat=True)


    # Start with base queryset
    events = Event.objects.all()

    # Apply search filter
    if search_query:
        events = events.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

    # Tag filter (manual)
    if tag_filter:
        events = events.filter(tags__id=tag_filter)

    # Date filters
    if start_date:
        events = events.filter(start_datetime__date__gte=start_date)
    if end_date:
        events = events.filter(start_datetime__date__lte=end_date)

    # Status filters
    if filter_choice == 'cancelled':
        events = events.filter(is_cancelled=True)
    elif filter_choice == 'moved':
        events = events.filter(is_moved=True)
    elif filter_choice == 'active':
        events = events.filter(is_cancelled=False, is_moved=False)
    elif filter_choice == 'all':
        pass  # No filtering applied, show all events
    else:
        filter_choice = 'all'


    # Sort
    if sort == 'latest':
        events = events.order_by('-created_at')
    elif sort == 'oldest':
        events = events.order_by('created_at')
    else:
        events = events.order_by('-start_datetime')


    # Separate views
    current_events = events.filter(start_datetime__date=current_date)
    past_events = events.all().order_by('-start_datetime')
    
    for_you_events_qs = Event.objects.filter(start_datetime__gte=current_date, start_datetime__lt=one_week_later)
    for_you_events = for_you_events_qs.filter(tags__skill_id__in=skill_ids)
    # Paginators
    paginator_current = Paginator(current_events, 10)
    paginator_past = Paginator(past_events, 10)
    paginator_foryou = Paginator(for_you_events, 10)

    page_obj_current = paginator_current.get_page(request.GET.get('page_current'))
    page_obj_past = paginator_past.get_page(request.GET.get('page_past'))
    page_obj_foryou = paginator_foryou.get_page(request.GET.get('page_foryou'))

    # Notifications and tags
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    all_tags = Tag.objects.all()

    context = {
        'profile': user_profile,
        'page_obj_current': page_obj_current,
        'page_obj_past': page_obj_past,
        'page_obj_foryou': page_obj_foryou,
        'current_date': current_date,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
        'all_tags': all_tags,
        'active_tab': active_tab,
        'sort': sort,
        'filter_choice': filter_choice,
        'search_query': search_query,
        'tag_filter': tag_filter,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'freelancer/event.html', context)

@login_required(login_url='user_login')
def event_attended_view(request):
    user_profile = get_object_or_404(Profile, account_id=request.user.account_id)

    # Prefetch user's attendance only
    attendance_qs = Attendance.objects.filter(user=request.user)
    user_attendances = Prefetch('attendances', queryset=attendance_qs, to_attr='user_attendances')

    # Fetch attended events with user's attendance only
    attended_events = (
        Event.objects
        .filter(attendances__user=request.user)
        .order_by('-start_datetime')
        .prefetch_related(user_attendances)
        .distinct()
    )

    # Group by event ID
    events_grouped = defaultdict(list)
    for event in attended_events:
        events_grouped[event.id].append(event)

    grouped_events = [{'event_id': key, 'events': value} for key, value in events_grouped.items()]

    # Pagination
    paginator = Paginator(grouped_events, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Notifications
    active_tab = 3
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    return render(request, 'freelancer/event_attended.html', {
        'profile': user_profile,
        'page_obj': page_obj,
        'active_tab': active_tab,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    })


@login_required(login_url='user_login')
def tag_filter_view(request, tag_id, account_id):
    user_profile = get_object_or_404(Profile, account_id=account_id)
    current_date = date.today()
    selected_tag = get_object_or_404(Tag, id=tag_id)
    filtered_announcements = Announcement.objects.filter(tags=selected_tag)
    all_announcements = Announcement.objects.all()
    all_tags = Tag.objects.all()
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    query = request.GET.get('q')
    if query:
        filtered_announcements = all_announcements.filter(Q(title__icontains=query) | Q(content__icontains=query))
    else:
        selected_tag_id = request.GET.get('tag')
        if selected_tag_id:
            selected_tag =  get_object_or_404(Tag, id=selected_tag_id)
            filtered_announcements = all_announcements.filter(tags__id=selected_tag_id)
            
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        announcements_today = announcements_today.filter(created_at__date__range=[start_date, end_date])
        announcements_foryou = announcements_foryou.filter(created_at__date__range=[start_date, end_date])

    all_announcements = Announcement.objects.order_by('-created_at')

    if start_date and end_date:
        all_announcements = all_announcements.filter(created_at__date__range=[start_date, end_date])
    
    context = {
        'filtered_announcements': filtered_announcements,
        'profile': user_profile,
        'selected_tag': selected_tag,
        'current_date': current_date,
        'all_tags': all_tags,
        'query': query,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }

    return render(request, 'freelancer/announcement_filtered.html', context)




@login_required(login_url='user_login')
def announcement_detail(request, announcement_id):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    announcement = get_object_or_404(Announcement, id=announcement_id)
    other_posts = Announcement.objects.exclude(id=announcement_id).order_by('-created_at')[:3]
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    context = {
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
        'announcement': announcement,
        'profile': user_profile,
        'other_posts': other_posts,
    }
    return render(request, 'freelancer/announcement_detail.html', context)


@login_required(login_url='user_login')
def event_detail_view(request, event_id):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    event = get_object_or_404(Event, id=event_id)

    # Fetch other posts
    other_posts = Event.objects.filter(is_published=True).exclude(id=event_id).order_by('-created_at')[:5]

    # Get unread notifications
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    # Handle RSVP
    if request.method == 'POST' and 'rsvp' in request.POST:
        rsvp_status = request.POST.get('rsvp_status', 'interested')
        RSVP.objects.update_or_create(
            user=request.user, event=event,
            defaults={'status': rsvp_status}
        )
        messages.success(request, format_html('Your RSVP status is now {}.', rsvp_status.capitalize()))

    # Handle attendance
    elif request.method == 'POST':
        current_time = timezone.now()

        if current_time < event.start_datetime:
            messages.error(request, f"{event.title} has not started yet. It will start on {event.start_datetime}.")
        elif current_time > event.end_datetime:
            messages.error(request, f"{event.title} has ended on {event.end_datetime}.")
        else:
            
            attendance, created = Attendance.objects.get_or_create(event=event, user=request.user, date=timezone.now().date())
            attendance.name = f"{user_profile.first_name} {user_profile.last_name}"
            attendance.logged_in = True
            attendance.gender = user_profile.gender[0].upper() if user_profile.gender else 'N'

            # Calculate age range
            if user_profile.date_of_birth:
                age = (timezone.now().date() - user_profile.date_of_birth).days // 365
                if age < 20:
                    attendance.age_range = 'A'
                elif 20 <= age <= 29:
                    attendance.age_range = 'B'
                elif 30 <= age <= 39:
                    attendance.age_range = 'C'
                elif 40 <= age <= 49:
                    attendance.age_range = 'D'
                else:
                    attendance.age_range = 'E'
            
            attendance.pwd = user_profile.is_pwd if user_profile else False
            attendance.four_ps = user_profile.is_4ps if user_profile else False

            attendance.affiliation = user_profile.bg_id.affiliation.aff_name if user_profile.bg_id and hasattr(user_profile.bg_id, 'affiliation') else ""
            attendance.contact = user_profile.contact_no
            attendance.email = request.user.email
            attendance.save()
            
        return redirect('event_detail_view', event_id=event_id)

    # Check if the user has already signed in today
    user_attendance = Attendance.objects.filter(event=event, user=request.user, date=timezone.now().date()).first()
    attendance_count = Attendance.objects.filter(event=event).aggregate(count=Count('id'))['count']

    # Get user RSVP
    user_rsvp = RSVP.objects.filter(event=event, user=request.user).first()
    rsvp_counts = event.rsvps.values('status').annotate(count=Count('id'))
    rsvp_dict = {
        'interested': 0,
        'attending': 0,
        'not_attending': 0,
    }
    for item in rsvp_counts:
        rsvp_dict[item['status']] = item['count']

    context = {
        'profile': user_profile,
        'event': event,
        'other_posts': other_posts,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
        'user_attendance': user_attendance,
        'attendance_count': attendance_count,
        'user_rsvp': user_rsvp,
        'rsvp_counts': rsvp_dict,  # Add RSVP counts to context
        'timezone_now': timezone.now(),
    }
    return render(request, 'freelancer/event_detail.html', context)



@login_required(login_url='user_login')
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()

    if notification.notification_type == 'announcement':
        return redirect('announcement_detail', announcement_id=notification.announcement.id)
    elif notification.notification_type == 'event':
        return redirect('event_detail_view', event_id=notification.event.id)
    elif notification.notification_type == 'support_ticket':
        return redirect('view_ticket', ticket_id=notification.support_ticket.id)
    
    # Fallback if notification type doesn't match any known types
    return redirect('index')

@login_required(login_url='user_login')
def tag_filter_event_view(request, tag_id, account_id):
    user_profile = get_object_or_404(Profile, account_id=account_id)
    current_date = date.today()
    selected_tag = get_object_or_404(Tag, id=tag_id)
    filtered_events = Event.objects.filter(tags=selected_tag)
    all_events = Event.objects.all()
    all_tags = Tag.objects.all()
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)  # Assuming you have a function to get notifications

    query = request.GET.get('q')
    if query:
        filtered_events = all_events.filter(Q(title__icontains=query) | Q(description__icontains=query))
    else:
        selected_tag_id = request.GET.get('tag')
        if selected_tag_id:
            selected_tag = get_object_or_404(Tag, id=selected_tag_id)
            filtered_events = all_events.filter(tags__id=selected_tag_id)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        filtered_events = filtered_events.filter(event_date__range=[start_date, end_date])
    
    context = {
        'filtered_events': filtered_events,
        'profile': user_profile,
        'selected_tag': selected_tag,
        'current_date': current_date,
        'all_tags': all_tags,
        'query': query,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }

    return render(request, 'freelancer/event_filtered.html', context)



@login_required(login_url='user_login')
def skills_view(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    skills = user_profile.bg_id.skills.all()
    skills_form = SkillsForm(request.POST or None)
    background_info = get_object_or_404(BackgroundInformation, bg_id=user_profile.bg_id_id)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    if request.method == 'POST':
        if 'skills_submit' in request.POST and skills_form.is_valid():
            if skills_form.is_valid():
                skill = skills_form.cleaned_data.get('skills') 
                for skill_obj in skill:
                    background_info.skills.add(skill_obj)
                background_info.save()
                messages.success(request, 'New Skill Added')
                return redirect('skills_view')
            else:
               for field, errors in skills_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error in field '{field}': {error}")

            return redirect('skills_view')
        elif 'remove_skill' in request.POST:
            skill_id = request.POST.get('remove_skill')
            skill_to_remove = Skills.objects.get(skill_id=skill_id)
            user_profile.bg_id.skills.remove(skill_to_remove)
            return redirect('skills_view')

    context = {
        'profile': user_profile,
        'skills': skills,
        'skills_form': skills_form,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }
    return render(request, 'freelancer/skills_view.html', context)

@login_required(login_url='user_login')
def languages_view(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    background_info = get_object_or_404(BackgroundInformation, bg_id=user_profile.bg_id_id)
    languages = background_info.backgroundinformationlanguage_set.all()
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    language_form = LanguageForm(request.POST or None)

    if request.method == 'POST':
        if 'language_submit' in request.POST and language_form.is_valid():
            selected_languages = language_form.cleaned_data.get('language')
            proficiency_level = request.POST.get('proficiency_level') or 'basic'  # ✅ default to basic

            for lang in selected_languages:
                bg_lang, created = BackgroundInformationLanguage.objects.get_or_create(
                    background_information=background_info,
                    language=lang,
                    defaults={'proficiency_level': proficiency_level}
                )
                if not created:
                    bg_lang.proficiency_level = proficiency_level
                    bg_lang.save()

            messages.success(request, 'Languages added/updated successfully.')
            return redirect('languages_view')

        elif 'remove_language' in request.POST:
            language_id = request.POST.get('remove_language')
            language_to_remove = get_object_or_404(Language, language_id=language_id)
            background_info_language = BackgroundInformationLanguage.objects.filter(
                background_information=background_info,
                language=language_to_remove
            ).first()
            if background_info_language:
                background_info_language.delete()
                messages.success(request, 'Language Removed Successfully')
            return redirect('languages_view')

    context = {
        'profile': user_profile,
        'languages': languages,
        'language_form': language_form,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }
    return render(request, 'freelancer/languages_view.html', context)


@login_required(login_url='user_login')
def update_language_view(request, language_id):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    language_instance = get_object_or_404(BackgroundInformationLanguage, id=language_id)

    if request.method == 'POST':
        update_form = UpdateLanguageForm(request.POST, instance=language_instance)
        if update_form.is_valid():
            update_form.save()
            messages.success(request, 'Language Updated Successfully')
            return redirect('languages_view')
    else:
        update_form = UpdateLanguageForm(instance=language_instance)

    context = {
        'update_language_form': update_form,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
        'language_instance': language_instance,
        'profile': user_profile,
    }
    return render(request, 'freelancer/update_language.html', context)

@login_required(login_url='user_login')
def experiences_view(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    experiences = user_profile.bg_id.past_experiences.all()
    past_experience_form = PastExperienceForm(request.POST or None)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    if request.method == 'POST':
        if 'remove_experience' in request.POST:
            experience_id = request.POST.get('remove_experience')
            experience_to_remove = PastExperience.objects.get(past_exp_id=experience_id)
            user_profile.bg_id.past_experiences.remove(experience_to_remove)
            experience_to_remove.delete()
            return redirect('experiences_view')

    context = {
        'profile': user_profile,
        'experiences': experiences,
        'past_experience_form': past_experience_form,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }
    return render(request, 'freelancer/experiences_view.html', context)



def add_experience_view(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    past_experience_form = PastExperienceForm(request.POST or None)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)


    if request.method == 'POST':
        if 'past_exp_submit' in request.POST and past_experience_form.is_valid():
            past_experience = past_experience_form.save(commit=False)
            past_experience.save()  # Save the past experience first
            user_profile.bg_id.past_experiences.add(past_experience)  # Add the experience to the user profile
            user_profile.bg_id.save()  # Save the user's background information
            return redirect('experiences_view')  # Redirect to the view that lists experiences

    context = {
        'profile': user_profile,
        'past_experience_form': past_experience_form,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }
    return render(request, 'freelancer/modals/add_experience.html', context)


@login_required(login_url='user_login')
def certificates_view(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    certificate_form = CertificateForm(request.POST or None, request.FILES or None)
    certificates = Certificate.objects.filter(profile=user_profile)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    # Handle certificate submission
    if 'certificate_submit' in request.POST:
        if certificate_form.is_valid():
            certificate = certificate_form.save(commit=False)
            certificate.profile = user_profile  # Ensure profile is always correctly set
            certificate.save()
            messages.success(request, 'Certificate Submission Successful')
            return redirect('certificates_view')
        else:
            messages.error(request, 'Certificate Submission Failed')

    # Handle certificate update
    if request.method == 'POST':
        for certificate in certificates:
            update_key = f'update_{certificate.id}'
            delete_key = f'delete_{certificate.id}'  # Define delete key for each certificate

            # Handle update
            if update_key in request.POST:
                form = CertificateForm(request.POST, request.FILES, instance=certificate, prefix=f'certificate_{certificate.id}')
                if form.is_valid():
                    certificate = form.save(commit=False)
                    certificate.profile = user_profile  # Explicitly set the profile again to prevent it from being null
                    certificate.save()
                    messages.success(request, f'Certificate "{certificate.certificate_title}" updated successfully.')
                else:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"Error in certificate '{certificate.certificate_title}', field '{field}': {error}")

                return redirect('certificates_view')

            # Handle deletion
            elif delete_key in request.POST:
                certificate.delete()
                messages.success(request, f'Certificate "{certificate.certificate_title}" deleted successfully.')
                return redirect('certificates_view')

    forms = {certificate.id: CertificateForm(instance=certificate, prefix=f'certificate_{certificate.id}') for certificate in certificates}

    context = {
        'forms': forms,
        'certificate_form': certificate_form,
        'certificates': certificates,
        'profile': user_profile,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }

    return render(request, 'freelancer/certificates_view.html', context)

@login_required(login_url='user_login')
def add_certificate_view(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    certificate_form = CertificateForm(request.POST or None, request.FILES or None)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    if request.method == 'POST' and 'certificate_submit' in request.POST:
        if certificate_form.is_valid():
            certificate = certificate_form.save(commit=False)
            certificate.profile = user_profile  # Ensure the certificate is linked to the user's profile
            certificate.save()
            messages.success(request, 'Certificate added successfully!')
            return redirect('certificates_view')  # Redirect to certificates list after successful submission
        else:
            messages.error(request, 'Error adding certificate. Please check the form.')
    
    context = {
        'certificate_form': certificate_form,
        'profile': user_profile,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    }
    return render(request, 'freelancer/modals/add_certificate.html', context)


@login_required(login_url='user_login')
def edit_certificate_view(request, certificate_id):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    certificate = get_object_or_404(Certificate, id=certificate_id, profile=user_profile)  # Ensure it's the user's certificate
    certificate_form = CertificateForm(request.POST or None, request.FILES or None, instance=certificate)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
        # Check if the file is a PDF or image
    is_pdf = False
    if certificate.image_file and certificate.image_file.url.endswith('.pdf'):
        is_pdf = True


    if request.method == 'POST' and 'certificate_submit' in request.POST:
        if certificate_form.is_valid():
            certificate = certificate_form.save(commit=False)
            certificate.profile = user_profile  # 🔹 Set the profile manually
            certificate.save()
            messages.success(request, 'Certificate added successfully!')
            return redirect('certificates_view')
        else:
            messages.error(request, 'Error updating certificate. Please check the form.')
    
    context = {
        'certificate_form': certificate_form,
        'certificate': certificate,
        'profile': user_profile,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
        'is_pdf': is_pdf,  # Pass whether the file is a PDF to the template

    }
    return render(request, 'freelancer/modals/add_certificate.html', context)


@login_required
def create_ticket(request):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)

    if request.method == 'POST':
        subject = request.POST.get('subject')
        other_subject = request.POST.get('other_subject', '').strip()
        # Use the 'Other' field if selected
        final_subject = other_subject if subject == "Other" else subject
        if final_subject:
            ticket = SupportTicket.objects.create(user=request.user, subject=final_subject)
            return redirect('view_ticket', ticket_id=ticket.id)

    # Fetch tickets for the user by status
    open_tickets = SupportTicket.objects.filter(user=request.user, status='open')
    in_progress_tickets = SupportTicket.objects.filter(user=request.user, status='in_progress')
    closed_tickets = SupportTicket.objects.filter(user=request.user, status='closed')

    # Pass the filtered tickets to the template
    return render(
        request, 
        'support_ticket/create_ticket.html', 
        {
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'closed_tickets': closed_tickets,
            'profile': user_profile,
            'notifications_unread': notifications_unread,
            'notifications_read': notifications_read,
        }
    )

@login_required
def view_ticket(request, ticket_id):
    user_profile = get_object_or_404(Profile, account_id=request.user)
    notifications_unread, notifications_read = get_notifications(user_profile.account_id.account_id)
    
    # Fetch the ticket and ensure it's linked to the current user
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    messages = ticket.messages.all()  # Get all messages related to the ticket

    # Mark unread messages as read
    for message in messages:
        if not message.is_read and message.sender != request.user:
            message.is_read = True
            message.save()

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.ticket = ticket  # Link the message to this specific ticket
            message.sender = request.user  # Set the sender as the current logged-in user
            message.save()
            return redirect('view_ticket', ticket_id=ticket.id)
    else:
        form = MessageForm()

    return render(request, 'support_ticket/view_ticket.html', {
        'ticket': ticket,
        'messages': messages,
        'form': form,
        'profile': user_profile,
        'notifications_unread': notifications_unread,
        'notifications_read': notifications_read,
    })

def handler404(request, exception):
    print(f"404 Error: Page not found. Path: {request.path}, Exception: {exception}")
    return render(request, '404.html', status=404)

def handler500(request):
    print(f"500 Error: Internal Server Error. Path: {request.path}")
    return render(request, '500.html', status=500)

def handler403(request, exception):
    print(f"403 Error: Forbidden. Path: {request.path}, Exception: {exception}")
    return render(request, '403.html', status=403)

def handler400(request, exception):
    print(f"400 Error: Bad Request. Path: {request.path}, Exception: {exception}")
    return render(request, '400.html', status=400)


def offline(request):
    return render(request, "offline.html")


def redirect_with_token(viewname, df_id, token):
    base_url = reverse(viewname, kwargs={'df_id': df_id})
    query_string = urlencode({'token': token})
    return redirect(f"{base_url}?{query_string}")

def edit_resume_and_projects(request, df_id):
    missing_items = []
    # ✅ Unified token retrieval (from GET or POST)
    token = request.GET.get('token') or request.POST.get('token')
    if request.method in ['GET', 'POST']:
        token = request.GET.get('token') or request.POST.get('token')
        if token:
            try:
                signer = TimestampSigner()
                unsigned_data = signer.unsign(token, max_age=60 * 60 * 24 * 14)
                data = loads(unsigned_data)
                token_df_id = str(data.get('df_id'))
                missing_items = data.get('missing_items', [])

                if str(df_id) != token_df_id:
                    messages.error(request, "Invalid access. Profile mismatch.")
                    return redirect('index')

            except SignatureExpired:
                messages.error(request, "Token Expired!")
                return redirect('index')

            except BadSignature:
                messages.error(request, "Token is Invalid!")
                return redirect('index')
        else:
            messages.error(request, "Token is missing.")


            return redirect('index')

    profile = get_object_or_404(Profile, df_id=df_id)
    resume_instance = Resume.objects.filter(profile=profile).first()
    project_instance = Project.objects.filter(profile=profile).first()

    if request.method == 'POST':
        resume_form = ResumeForm(request.POST, request.FILES, instance=resume_instance)
        project_form = ProjectForm(request.POST, request.FILES, instance=project_instance)
        # Prevent submission if editing fields not in missing_items
        if 'resume' not in missing_items and 'resume_file' in request.FILES:
            messages.error(request, "You are not allowed to update the resume.")
            return redirect_with_token('edit_resume_projects', profile.df_id, token)

        if 'projects/Portfolio' not in missing_items and (
            request.POST.get('title') or request.POST.get('description') or 'pdf_file' in request.FILES
        ):
            print("missing_items:", missing_items)
            print("title:", request.POST.get('title'))
            print("description:", request.POST.get('description'))
            print("file:", request.FILES.get('pdf_file'))

            messages.error(request, "You are not allowed to update the project.")
            return redirect_with_token('edit_resume_projects', profile.df_id, token)

        if resume_form.is_valid() and project_form.is_valid():
            resume = resume_form.save(commit=False)
            resume.profile = profile
            resume.save()

            project = project_form.save(commit=False)
            project.profile = profile
            project.save()

            messages.success(request, "Resume and project updated successfully.")
            return redirect_with_token('edit_resume_projects', profile.df_id, token)
        else:

            messages.error(request, "There was an error in your submission. Please check the fields.")
    else:
        resume_form = ResumeForm(instance=resume_instance)
        project_form = ProjectForm(instance=project_instance)

    step_number = 4

    return render(request, 'profile/edit_resume_projects.html', {
        'step_number': step_number,
        'resume_form': resume_form,
        'project_form': project_form,
        'missing_items': json.dumps(missing_items),
        'df_id': df_id,
        'resume_file_name': resume_instance.resume_file.name.split('/')[-1] if resume_instance and resume_instance.resume_file else '',
        'project_file_name': project_instance.pdf_file.name.split('/')[-1] if project_instance and project_instance.pdf_file else '',
        'token': token,
    })
