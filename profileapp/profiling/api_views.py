from django.http import JsonResponse
from .models import Profile, Skills, Language, Specialization, Language, Skills, Tag 
from geolocations.models import City, Barangay
from events.models import Event, Attendance, RSVP
from django.db.models import Count, Max, F, FloatField, ExpressionWrapper
from django.shortcuts import render
import requests
from django.http import FileResponse, Http404
from .models import Project
from django.shortcuts import render,  redirect, get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from collections import defaultdict
from profiling.models import Account

from support.models import Message, SupportTicket, Notification
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from .helpers import (
    get_filtered_events,
    aggregate_event_statistics,
    calculate_rsvp_statistics,
    calculate_rsvp_to_attendance,
    calculate_summary_statistics
)
def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def get_freelancer_count(request):
    general_santos_city = City.objects.get(city='General Santos City')
    freelancer_count = Profile.objects.filter(city=general_santos_city).count()
    return JsonResponse({'freelancer_count': freelancer_count})
@user_passes_test(is_admin)
def get_freelancer_count_per_barangay(request):
    freelancer_counts = (
        Profile.objects.values('barangay__barangay')
        .annotate(freelancer_count=Count('account_id'))
        .order_by('barangay__barangay')
    )
    data = {item['barangay__barangay']: item['freelancer_count'] for item in freelancer_counts}
    return JsonResponse(data)

@user_passes_test(is_admin)
def get_dominant_details_per_barangay(request):
    barangays = Profile.objects.values('barangay__barangay', 'barangay__barangay_id').distinct()

    data = {}
    for barangay in barangays:
        barangay_name = barangay['barangay__barangay']
        barangay_id = barangay['barangay__barangay_id']

        # Get the fun fact
        fun_fact = Barangay.objects.get(barangay_id=barangay_id).fun_fact

        # Get the dominant skill and top 3 skills
        skill_counts = (
            Profile.objects.filter(barangay_id=barangay_id, bg_id__isnull=False)
            .values('bg_id__skills__skill')
            .annotate(count=Count('bg_id__skills__skill'))
            .order_by('-count')
        )
        dominant_skill = skill_counts[0]['bg_id__skills__skill'] if skill_counts else None
        top_skills = [{'skill': skill['bg_id__skills__skill'], 'count': skill['count']} for skill in skill_counts[:3]]

        # Get the dominant language and top 3 languages
        language_counts = (
            Profile.objects.filter(barangay_id=barangay_id, bg_id__isnull=False)
            .values('bg_id__language__language')
            .annotate(count=Count('bg_id__language__language'))
            .order_by('-count')
        )
        dominant_language = language_counts[0]['bg_id__language__language'] if language_counts else None
        top_languages = [{'language': language['bg_id__language__language'], 'count': language['count']} for language in language_counts[:3]]

        # Get the dominant specialization and top 3 specializations
        specialization_counts = (
            Profile.objects.filter(barangay_id=barangay_id, bg_id__isnull=False)
            .values('bg_id__specialization__specialization')
            .annotate(count=Count('bg_id__specialization__specialization'))
            .order_by('-count')
        )
        dominant_specialization = specialization_counts[0]['bg_id__specialization__specialization'] if specialization_counts else None
        top_specializations = [{'specialization': specialization['bg_id__specialization__specialization'], 'count': specialization['count']} for specialization in specialization_counts[:3]]

        data[barangay_name] = {
            'fun_fact': fun_fact,
            'dominant_skill': dominant_skill,
            'top_skills': top_skills,
            'dominant_language': dominant_language,
            'top_languages': top_languages,
            'dominant_specialization': dominant_specialization,
            'top_specializations': top_specializations
        }

    return JsonResponse(data)

def get_languages_and_skills(request):
    languages = list(Language.objects.values('language_id', 'language'))
    skills = list(Skills.objects.values('skill_id', 'skill'))
    tags = list(Tag.objects.filter(skills__isnull=False).distinct().values('id', 'name'))
    return JsonResponse({'languages': languages, 'skills': skills, 'tags': tags})

def events_api(request):
    events = Event.objects.filter(is_cancelled=False, is_published=True)
    events_list = []
    for event in events:
        events_list.append({
            'id': event.pk,
            'title': event.title,
            'description': event.description,
            'start_datetime': event.start_datetime.isoformat(),
            'end_datetime': event.end_datetime.isoformat(),
            'location': {
                'name': event.location.name if event.location else None,
                'latitude': event.location.latitude if event.location else None,
                'longitude': event.location.longitude if event.location else None,
            } if event.location else None,
            'type': event.location_type,
            'organizer': event.organizer,
            'virtual_details': event.virtual_details.url if event.virtual_details else None,
            'image': event.image.url if event.image else None,  # Include image URL
        })
    return JsonResponse(events_list, safe=False)


def latest_event_statistics(request):
    # Get the latest published event
    latest_event = Event.objects.filter(is_published=True).order_by('-start_datetime').first()
    
    if not latest_event:
        return JsonResponse({"error": "No events found."}, status=404)

    # Get total number of attendees
    total_attendees = Attendance.objects.filter(event=latest_event).count()

    # Get attendance data by date for the event
    attendance_by_date = (
        Attendance.objects.filter(event=latest_event)
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Gender ratio
    gender_counts = (
        Attendance.objects.filter(event=latest_event)
        .values('gender')
        .annotate(count=Count('id'))
    )

    # Count and percentage of PWD and 4Ps attendees
    pwd_count = Attendance.objects.filter(event=latest_event, pwd=True).count()
    four_ps_count = Attendance.objects.filter(event=latest_event, four_ps=True).count()
    pwd_percentage = (pwd_count / total_attendees * 100) if total_attendees > 0 else 0
    four_ps_percentage = (four_ps_count / total_attendees * 100) if total_attendees > 0 else 0

    # Percentage of freelancers with matching skills
    tag_skill_ids = latest_event.tags.values_list('skill_id', flat=True)
    freelancer_with_skills_count = Attendance.objects.filter(
        event=latest_event,
        user__profile__bg_id__skills__skill_id__in=tag_skill_ids
    ).distinct().count()
    matching_skills_percentage = (
        (freelancer_with_skills_count / total_attendees) * 100 if total_attendees else 0
    )

    # Count and percentage for each RSVP status
    total_rsvps = RSVP.objects.filter(event=latest_event).count()
    rsvp_counts = RSVP.objects.filter(event=latest_event).values('status').annotate(count=Count('id'))
    rsvp_statuses = {status['status']: status['count'] for status in rsvp_counts}
    
    interested_count = rsvp_statuses.get('interested', 0)
    attending_count = rsvp_statuses.get('attending', 0)
    not_attending_count = rsvp_statuses.get('not_attending', 0)
        
    interested_percentage = (interested_count / total_rsvps * 100) if total_rsvps > 0 else 0
    attending_percentage = (attending_count / total_rsvps * 100) if total_rsvps > 0 else 0
    not_attending_percentage = (not_attending_count / total_rsvps * 100) if total_rsvps > 0 else 0

    # Count of RSVPs converted to attendance
    attending_rsvps = RSVP.objects.filter(event=latest_event, status='attending')
    rsvp_to_attendance_count = Attendance.objects.filter(
        event=latest_event,
        user__in=attending_rsvps.values_list('user', flat=True)
    ).count()
    total_rsvp = attending_count + interested_count
    rsvp_to_attendance_percentage = (
        (rsvp_to_attendance_count / total_rsvp) * 100 if total_rsvp > 0 else 0
    )


    age_distribution = (
        Attendance.objects.filter(event=latest_event)
        .values('age_range')
        .annotate(count=Count('id'))
        .order_by('age_range')
    )

    # Add this to the data response
    # JSON structure for the response
    data = {
        "title": latest_event.title,
        "start_datetime": latest_event.start_datetime,
        "attendance_by_date": list(attendance_by_date),
        "gender_ratio": list(gender_counts),
        "age_distribution": list(age_distribution),
        "total_attendees": total_attendees,
        "pwd_count": pwd_count,
        "pwd_percentage": pwd_percentage,
        "four_ps_count": four_ps_count,
        "four_ps_percentage": four_ps_percentage,
        "matching_skills_percentage": matching_skills_percentage,
        "interested_count": interested_count,
        "attending_count": attending_count,
        "not_attending_count": not_attending_count,
        "interested_percentage": interested_percentage,
        "attending_percentage": attending_percentage,
        "not_attending_percentage": not_attending_percentage,
        "rsvp_to_attendance_count": rsvp_to_attendance_count,
        "rsvp_to_attendance_percentage": rsvp_to_attendance_percentage
    }

    return JsonResponse(data)

@user_passes_test(is_admin)
def barangay_breakdown(request, barangay_name):
    # Get the freelancer count for the specified barangay
    freelancer_count = Profile.objects.filter(barangay__barangay=barangay_name).count()

    # Get a limited number of names of people in the specified barangay
    people = Profile.objects.filter(barangay__barangay=barangay_name)

    # Get all the skills, languages, and specializations in the specified barangay
    skills = (
        Profile.objects.filter(barangay__barangay=barangay_name, bg_id__isnull=False)
        .values('bg_id__skills__skill')
        .annotate(count=Count('bg_id__skills__skill'))
        .order_by('-count')
    )

    languages = (
        Profile.objects.filter(barangay__barangay=barangay_name, bg_id__isnull=False)
        .values('bg_id__language__language')
        .annotate(count=Count('bg_id__language__language'))
        .order_by('-count')
    )

    specializations = (
        Profile.objects.filter(barangay__barangay=barangay_name, bg_id__isnull=False)
        .values('bg_id__specialization__specialization')
        .annotate(count=Count('bg_id__specialization__specialization'))
        .order_by('-count')
    )

    context = {
        'barangay_name': barangay_name,
        'freelancer_count': freelancer_count,
        'people': people,
        'skills': skills,
        'languages': languages,
        'specializations': specializations,
    }

    return render(request, 'admin/barangay_breakdown.html', context)

@user_passes_test(is_admin)
def index_barangay_breakdown(request):
    # Total freelancer count
    freelancer_count = Profile.objects.count() or 1  # Avoid division by zero by defaulting to 1 if count is zero

    # Aggregate freelancers by barangay with count and percentage
    barangays = (
        Profile.objects.values('barangay__barangay')  # Assuming `barangay__barangay` is the barangay name field
        .annotate(
            count=Count('df_id'),
            percentage=ExpressionWrapper(
                Count('df_id') * 100.0 / freelancer_count,
                output_field=FloatField()
            )
        )
        .order_by('-count')
    )

    # Aggregate skills with count and percentage
    skills = (
        Profile.objects.filter(bg_id__isnull=False)
        .values('bg_id__skills__skill')
        .annotate(
            count=Count('bg_id__skills__skill'),
            percentage=ExpressionWrapper(
                Count('bg_id__skills__skill') * 100.0 / freelancer_count,
                output_field=FloatField()
            )
        )
        .order_by('-count')
    )

    # Aggregate languages with count and percentage
    languages = (
        Profile.objects.filter(bg_id__isnull=False)
        .values('bg_id__language__language')
        .annotate(
            count=Count('bg_id__language__language'),
            percentage=ExpressionWrapper(
                Count('bg_id__language__language') * 100.0 / freelancer_count,
                output_field=FloatField()
            )
        )
        .order_by('-count')
    )

    # Aggregate specializations with count and percentage
    specializations = (
        Profile.objects.filter(bg_id__isnull=False)
        .values('bg_id__specialization__specialization')
        .annotate(
            count=Count('bg_id__specialization__specialization'),
            percentage=ExpressionWrapper(
                Count('bg_id__specialization__specialization') * 100.0 / freelancer_count,
                output_field=FloatField()
            )
        )
        .order_by('-count')
    )

    # Structure the data into a dictionary for easy JSON serialization
    data = {
        'freelancer_count': freelancer_count,
        'barangays': list(barangays),  # Include barangay breakdown
        'skills': list(skills),
        'languages': list(languages),
        'specializations': list(specializations),
    }

    return JsonResponse(data, safe=False)

def filter_skills_by_tags(request):
    tag_names = request.GET.getlist('tags')
    skills = Skills.objects.filter(tags__name__in=tag_names).distinct().values('skill_id', 'skill')

    return JsonResponse({'skills': list(skills)})


@xframe_options_exempt  # This allows the specific view to be loaded in an iframe
def pdf_preview(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    pdf_file = project.pdf_file
    if not pdf_file:
        raise Http404("No PDF found for this project")
    
    return FileResponse(open(pdf_file.path, 'rb'), content_type='application/pdf')


def latest_tickets_with_message(request):
    """
    Fetch tickets with their latest message, filtered by status, with pagination support.
    """
    status = request.GET.get('status', '')
    tickets = SupportTicket.objects.all().prefetch_related('messages')
    
    if status:
        tickets = tickets.filter(status=status)

    # Paginate tickets
    page_number = request.GET.get('page', 1)
    paginator = Paginator(tickets, 5)  # 5 tickets per page
    page_obj = paginator.get_page(page_number)

    # Prepare ticket data
    data = []
    for ticket in page_obj:
        latest_message = ticket.messages.order_by('-created_at').first()
        if latest_message:
            data.append({
                'ticket_id': ticket.id,
                'subject': ticket.subject,
                'status': ticket.status,  # Add status to response
                'sender': latest_message.sender.username if latest_message.sender else 'Unknown',
                'message': latest_message.message,
                'created_at': latest_message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

    return JsonResponse({
        'data': data,
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
    }, safe=False)


@login_required
def event_statistics(request, event_id):
    # Get the specified event by ID
    event = get_object_or_404(Event, id=event_id, is_published=True)

    # Get total number of attendees
    total_attendees = Attendance.objects.filter(event=event).count()

    # Get attendance data by date for the event
    attendance_by_date = (
        Attendance.objects.filter(event=event)
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Gender ratio
    gender_counts = (
        Attendance.objects.filter(event=event)
        .values('gender')
        .annotate(count=Count('id'))
    )

    # Count and percentage of PWD and 4Ps attendees
    pwd_count = Attendance.objects.filter(event=event, pwd=True).count()
    four_ps_count = Attendance.objects.filter(event=event, four_ps=True).count()
    pwd_percentage = (pwd_count / total_attendees * 100) if total_attendees > 0 else 0
    four_ps_percentage = (four_ps_count / total_attendees * 100) if total_attendees > 0 else 0

    # Percentage of freelancers with matching skills
    tag_skill_ids = event.tags.values_list('skill_id', flat=True)
    freelancer_with_skills_count = Attendance.objects.filter(
        event=event,
        user__profile__bg_id__skills__skill_id__in=tag_skill_ids
    ).distinct().count()
    matching_skills_percentage = (
        (freelancer_with_skills_count / total_attendees) * 100 if total_attendees else 0
    )

    # Count and percentage for each RSVP status
    total_rsvps = RSVP.objects.filter(event=event).count()
    rsvp_counts = RSVP.objects.filter(event=event).values('status').annotate(count=Count('id'))
    rsvp_statuses = {status['status']: status['count'] for status in rsvp_counts}

    interested_count = rsvp_statuses.get('interested', 0)
    attending_count = rsvp_statuses.get('attending', 0)
    not_attending_count = rsvp_statuses.get('not_attending', 0)

    interested_percentage = (interested_count / total_rsvps * 100) if total_rsvps > 0 else 0
    attending_percentage = (attending_count / total_rsvps * 100) if total_rsvps > 0 else 0
    not_attending_percentage = (not_attending_count / total_rsvps * 100) if total_rsvps > 0 else 0

    # Count of RSVPs converted to attendance
    attending_rsvps = RSVP.objects.filter(event=event, status='attending')
    rsvp_to_attendance_count = Attendance.objects.filter(
        event=event,
        user__in=attending_rsvps.values_list('user', flat=True)
    ).count()
    total_rsvp = attending_count + interested_count
    rsvp_to_attendance_percentage = (
        (rsvp_to_attendance_count / total_rsvp) * 100 if total_rsvp > 0 else 0
    )

    # Age range distribution
    age_distribution = (
        Attendance.objects.filter(event=event)
        .values('age_range')
        .annotate(count=Count('id'))
        .order_by('age_range')
    )

    # Attendance list with detailed information
    attendance_list = list(Attendance.objects.filter(event=event).values(
        'name', 'date', 'age_range', 'gender', 'pwd', 'four_ps', 'affiliation'
    ))

    # RSVP list with detailed information
    rsvp_list = list(RSVP.objects.filter(event=event).values(
        'user__username', 'status', 'timestamp'
    ))

    # JSON structure for the response
    data = {
        "title": event.title,
        "start_datetime": event.start_datetime,
        "attendance_by_date": list(attendance_by_date),
        "gender_ratio": list(gender_counts),
        "age_distribution": list(age_distribution),
        "total_attendees": total_attendees,
        "pwd_count": pwd_count,
        "pwd_percentage": pwd_percentage,
        "four_ps_count": four_ps_count,
        "four_ps_percentage": four_ps_percentage,
        "matching_skills_percentage": matching_skills_percentage,
        "interested_count": interested_count,
        "attending_count": attending_count,
        "not_attending_count": not_attending_count,
        "interested_percentage": interested_percentage,
        "attending_percentage": attending_percentage,
        "not_attending_percentage": not_attending_percentage,
        "rsvp_to_attendance_count": rsvp_to_attendance_count,
        "rsvp_to_attendance_percentage": rsvp_to_attendance_percentage,
        "attendance": attendance_list,  # Added detailed attendance list
        "rsvp": rsvp_list  # Added detailed RSVP list
    }

    return JsonResponse(data)

@login_required
def event_count_api(request):
    total_events = Event.objects.count()
    return JsonResponse({'total_events': total_events})

@login_required
def overall_event_statistics(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    events = get_filtered_events(start_date, end_date)
    stats = aggregate_event_statistics(events)
    rsvp_stats = calculate_rsvp_statistics(events)
    rsvp_to_attendance = calculate_rsvp_to_attendance(events)
    summary_stats = calculate_summary_statistics(events)

    total_rsvp_for_percentage = rsvp_stats["attending_count"] + rsvp_stats["interested_count"]
    rsvp_to_attendance_percentage = (rsvp_to_attendance / total_rsvp_for_percentage * 100) if total_rsvp_for_percentage > 0 else 0

    response_data = {
        **summary_stats,
        **rsvp_stats,
        "total_attendees": stats["total_attendees"],
        "pwd_count": stats["pwd_count"],
        "pwd_percentage": (stats["pwd_count"] / stats["total_attendees"] * 100) if stats["total_attendees"] > 0 else 0,
        "four_ps_count": stats["four_ps_count"],
        "four_ps_percentage": (stats["four_ps_count"] / stats["total_attendees"] * 100) if stats["total_attendees"] > 0 else 0,
        "matching_skills_percentage": (stats["matching_skills_count"] / stats["total_attendees"] * 100) if stats["total_attendees"] > 0 else 0,
        "attendance_by_event": stats["attendance_by_event"],  # 🔥 Directly return it
        "age_distribution": [{'age_range': age_range, 'count': count} for age_range, count in stats["age_distribution"].items()],
        "gender_ratio": [{'gender': gender, 'count': count} for gender, count in stats["gender_counts"].items()],
        "interested_percentage": (rsvp_stats["interested_count"] / rsvp_stats["total_rsvps"] * 100) if rsvp_stats["total_rsvps"] > 0 else 0,
        "attending_percentage": (rsvp_stats["attending_count"] / rsvp_stats["total_rsvps"] * 100) if rsvp_stats["total_rsvps"] > 0 else 0,
        "not_attending_percentage": (rsvp_stats["not_attending_count"] / rsvp_stats["total_rsvps"] * 100) if rsvp_stats["total_rsvps"] > 0 else 0,
        "rsvp_to_attendance_count": rsvp_to_attendance,
        "rsvp_to_attendance_percentage": rsvp_to_attendance_percentage,
        "attendance": stats["attendance_list"],
        "rsvp": stats["rsvp_list"],
        "tags": list(Skills.objects.values('skill_id', 'skill'))  # If you want to fetch all tags

    }

    return JsonResponse(response_data)

@login_required
@csrf_exempt
def unread_messages_count(request):
    """
    API endpoint to return the count of unread messages for the logged-in user.
    """
    user = request.user
    # Count unread messages that are not sent by the user
    unread_count = Message.objects.filter(
        is_read=False
    ).exclude(
        sender=user
    ).exclude(
        sender__is_staff=True
    ).count()

    return JsonResponse({'unread_count': unread_count})

@login_required
@csrf_exempt
def mark_messages_as_read(request, ticket_id):
    if request.method == 'POST':
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        unread_messages = ticket.messages.filter(is_read=False).exclude(sender=request.user)
        unread_messages.update(is_read=True)
        return JsonResponse({'status': 'success', 'message': 'All unread messages marked as read.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@login_required
@csrf_exempt
def add_message_to_conversation(request, ticket_id):
    """
    API to add a new message to a specific conversation.
    """
    if request.method == 'POST':
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        message_content = request.POST.get('message')
        if message_content:
            message = Message.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message_content,
                is_read=False
            )
            return JsonResponse({'status': 'success', 'message': 'Message added', 'message_id': message.id})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def mark_all_notifications_as_read(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])
        notifications = Notification.objects.filter(id__in=notification_ids, user=request.user, is_read=False)
        notifications.update(is_read=True)
        return JsonResponse({'status': 'success', 'message': 'All notifications marked as read.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)


@login_required
def unverified_users_count(request):
    count = Account.objects.filter(is_verified=False).count()
    return JsonResponse({'unverified_users': count})



@login_required
def admin_latest_notifications(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    data = [
        {
            'message': n.message,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': n.is_read
        }
        for n in notifications
    ]
    return JsonResponse(data, safe=False)


from django.utils.decorators import method_decorator
from django.views import View
@method_decorator(csrf_exempt, name='dispatch')
class MarkSingleNotificationReadView(View):
    def post(self, request, notif_id):
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        try:
            notif = Notification.objects.get(pk=notif_id, user=request.user)
            notif.is_read = True
            notif.save()
            return JsonResponse({'status': 'success'})
        except Notification.DoesNotExist:
            return JsonResponse({'error': 'Notification not found'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class MarkAllReadView(View):
    def post(self, request):
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})