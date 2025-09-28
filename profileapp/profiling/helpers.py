from collections import defaultdict
from django.db.models import Count
from django.utils.dateparse import parse_date

from events.models import Event, Attendance, RSVP

def get_filtered_events(start_date, end_date):
    events = Event.objects.filter(is_published=True)
    if start_date:
        events = events.filter(start_datetime__gte=parse_date(start_date))
    if end_date:
        events = events.filter(end_datetime__lte=parse_date(end_date))
    return events

def aggregate_event_statistics(events):
    from collections import defaultdict

    total_attendees = 0
    pwd_count = 0
    four_ps_count = 0
    matching_skills_count = 0
    attendance_by_date = defaultdict(int)
    age_distribution = defaultdict(int)
    gender_counts = defaultdict(int)
    attendance_list = []
    rsvp_list = []
    attendance_by_event_list = []

    for event in events:
        attendances = Attendance.objects.filter(event=event)
        rsvps = RSVP.objects.filter(event=event)

        event_total_attendees = attendances.count()
        event_pwd_count = attendances.filter(pwd=True).count()
        event_four_ps_count = attendances.filter(four_ps=True).count()

        total_attendees += event_total_attendees
        pwd_count += event_pwd_count
        four_ps_count += event_four_ps_count

        tag_skill_ids = list(event.tags.values_list('skill_id', flat=True))
        matching_skills_count += attendances.filter(
            user__profile__bg_id__skills__skill_id__in=tag_skill_ids
        ).distinct().count()

        # ✅ Initialize per-event distributions
        event_age_distribution = defaultdict(int)
        event_gender_distribution = defaultdict(int)
        event_pwd_distribution_by_age = defaultdict(int)
        event_pwd_distribution_by_gender = defaultdict(int)
        event_fourps_distribution_by_age = defaultdict(int)
        event_fourps_distribution_by_gender = defaultdict(int)

        for att in attendances:
            # ✅ Global counters
            attendance_by_date[event.title] += 1
            age_distribution[att.age_range] += 1
            gender_counts[att.gender] += 1

            # ✅ Per-event counters
            event_age_distribution[att.age_range] += 1
            event_gender_distribution[att.gender] += 1

            if att.pwd:
                event_pwd_distribution_by_age[att.age_range] += 1
                event_pwd_distribution_by_gender[att.gender] += 1

            if att.four_ps:
                event_fourps_distribution_by_age[att.age_range] += 1
                event_fourps_distribution_by_gender[att.gender] += 1

            attendance_list.append({
                'name': att.name,
                'date': att.date,
                'age_range': att.age_range,
                'gender': att.gender,
                'pwd': att.pwd,
                'four_ps': att.four_ps,
                'affiliation': att.affiliation or '-'
            })

        for rsvp in rsvps:
            rsvp_list.append({
                'user': rsvp.user.username,
                'status': rsvp.status,
                'timestamp': rsvp.timestamp
            })

        # ✅ Save per-event summarized statistics
        attendance_by_event_list.append({
            'event': event.title,
            'count': event_total_attendees,
            'tags': tag_skill_ids,
            'pwd_count': event_pwd_count,
            'four_ps_count': event_four_ps_count,
            'age_distribution': dict(event_age_distribution),
            'gender_distribution': dict(event_gender_distribution),
            'pwd_distribution_by_age': dict(event_pwd_distribution_by_age),
            'pwd_distribution_by_gender': dict(event_pwd_distribution_by_gender),
            'four_ps_distribution_by_age': dict(event_fourps_distribution_by_age),
            'four_ps_distribution_by_gender': dict(event_fourps_distribution_by_gender),
        })

    return {
        "total_attendees": total_attendees,
        "pwd_count": pwd_count,
        "four_ps_count": four_ps_count,
        "matching_skills_count": matching_skills_count,
        "attendance_by_event": attendance_by_event_list,
        "age_distribution": age_distribution,
        "gender_counts": gender_counts,
        "attendance_list": attendance_list,
        "rsvp_list": rsvp_list
    }

def calculate_rsvp_statistics(events):
    total_rsvps = RSVP.objects.filter(event__in=events).count()
    rsvp_status_counts = RSVP.objects.filter(event__in=events).values('status').annotate(count=Count('id'))
    rsvp_status_dict = {status['status']: status['count'] for status in rsvp_status_counts}

    interested = rsvp_status_dict.get('interested', 0)
    attending = rsvp_status_dict.get('attending', 0)
    not_attending = rsvp_status_dict.get('not_attending', 0)

    return {
        "total_rsvps": total_rsvps,
        "interested_count": interested,
        "attending_count": attending,
        "not_attending_count": not_attending,
    }

def calculate_rsvp_to_attendance(events):
    attended_users = Attendance.objects.filter(event__in=events).values_list('user', flat=True)

    attending = RSVP.objects.filter(event__in=events, status='attending', user__in=attended_users).count()
    interested = RSVP.objects.filter(event__in=events, status='interested', user__in=attended_users).count()
    not_attending = RSVP.objects.filter(event__in=events, status='not_attending', user__in=attended_users).count()

    return attending + interested + not_attending

def calculate_summary_statistics(events):
    total_event_count = events.count()
    total_rsvp_count = RSVP.objects.filter(event__in=events).count()
    total_attendance_count = Attendance.objects.filter(event__in=events).count()

    average_rsvp_per_event = total_rsvp_count / total_event_count if total_event_count > 0 else 0
    average_attendance_per_event = total_attendance_count / total_event_count if total_event_count > 0 else 0

    return {
        "total_event_count": total_event_count,
        "total_rsvp_count": total_rsvp_count,
        "total_attendance_count": total_attendance_count,
        "average_rsvp_per_event": average_rsvp_per_event,
        "average_attendance_per_event": average_attendance_per_event
    }
