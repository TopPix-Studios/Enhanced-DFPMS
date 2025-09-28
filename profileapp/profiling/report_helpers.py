from collections import defaultdict
from datetime import date
from profiling.models import Profile, BackgroundInformationLanguage
from django.db.models import Count

def calculate_age(birth_date):
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def get_age_group(age):
    if age <= 20:
        return '20 and below'
    elif 21 <= age <= 29:
        return '20–29'
    elif 30 <= age <= 39:
        return '30–39'
    elif 40 <= age <= 49:
        return '40–49'
    else:
        return '50 and above'

def get_skill_breakdowns(background_info_qs):
    gender_breakdown = defaultdict(lambda: {'Male': 0, 'Female': 0, 'Others': 0})
    barangay_breakdown = defaultdict(lambda: defaultdict(int))
    age_breakdown = defaultdict(lambda: defaultdict(int))

    # Fetch profiles and relate them via bg_id
    profiles_by_bg_id = {
        profile.bg_id_id: profile
        for profile in Profile.objects.select_related('barangay').all()
        if profile.bg_id_id is not None
    }

    # Prefetch skills for performance
    background_info_qs = background_info_qs.prefetch_related('skills')
    for info in background_info_qs:
        profile = profiles_by_bg_id.get(info.bg_id)
        if not profile:
            continue

        gender = (profile.gender or 'Others').title()
        barangay = profile.barangay.barangay if profile.barangay else 'Unspecified'

        try:
            age = calculate_age(profile.date_of_birth)
            age_group = get_age_group(age)
        except (TypeError, AttributeError):
            age_group = 'Unknown'

        for sk in info.skills.all():
            if sk.skill:
                skill_name = sk.skill
                gender_breakdown[skill_name][gender] += 1
                barangay_breakdown[skill_name][barangay] += 1
                age_breakdown[skill_name][age_group] += 1

    return {
        'gender_breakdown': dict(gender_breakdown),
        'barangay_breakdown': {k: dict(v) for k, v in barangay_breakdown.items()},
        'age_breakdown': {k: dict(v) for k, v in age_breakdown.items()},
    }


def get_specialization_breakdowns(background_info_qs):
    gender_breakdown = defaultdict(lambda: {'Male': 0, 'Female': 0, 'Others': 0})
    barangay_breakdown = defaultdict(lambda: defaultdict(int))
    age_breakdown = defaultdict(lambda: defaultdict(int))

    profiles_by_bg_id = {
        profile.bg_id_id: profile
        for profile in Profile.objects.select_related('barangay').all()
        if profile.bg_id_id is not None
    }

    background_info_qs = background_info_qs.select_related('specialization').all()
    for info in background_info_qs:
        profile = profiles_by_bg_id.get(info.bg_id)
        if not profile or not info.specialization:
            continue

        specialization = info.specialization.specialization
        gender = (profile.gender or 'Others').title()
        barangay = profile.barangay.barangay if profile.barangay else 'Unspecified'

        try:
            age = calculate_age(profile.date_of_birth)
            age_group = get_age_group(age)
        except (TypeError, AttributeError):
            age_group = 'Unknown'

        gender_breakdown[specialization][gender] += 1
        barangay_breakdown[specialization][barangay] += 1
        age_breakdown[specialization][age_group] += 1

    return {
        'gender_breakdown': dict(gender_breakdown),
        'barangay_breakdown': {k: dict(v) for k, v in barangay_breakdown.items()},
        'age_breakdown': {k: dict(v) for k, v in age_breakdown.items()},
    }

def get_language_breakdowns(background_info_qs):
    gender_breakdown = defaultdict(lambda: {'Male': 0, 'Female': 0, 'Others': 0})
    barangay_breakdown = defaultdict(lambda: defaultdict(int))
    age_breakdown = defaultdict(lambda: defaultdict(int))

    # Fetch profiles with bg_id map
    profiles_by_bg_id = {
        profile.bg_id_id: profile
        for profile in Profile.objects.select_related('barangay').all()
        if profile.bg_id_id is not None
    }

    # Get BackgroundInformationLanguage entries for the filtered queryset
    language_entries = (
        BackgroundInformationLanguage.objects
        .select_related('language', 'background_information')
        .filter(background_information__in=background_info_qs)
    )

    for entry in language_entries:
        info = entry.background_information
        profile = profiles_by_bg_id.get(info.bg_id)
        if not profile or not entry.language:
            continue

        language_name = entry.language.language or 'Unspecified'
        gender = (profile.gender or 'Others').title()
        barangay = profile.barangay.barangay if profile.barangay else 'Unspecified'

        try:
            age = calculate_age(profile.date_of_birth)
            age_group = get_age_group(age)
        except (TypeError, AttributeError):
            age_group = 'Unknown'

        gender_breakdown[language_name][gender] += 1
        barangay_breakdown[language_name][barangay] += 1
        age_breakdown[language_name][age_group] += 1

    return {
        'gender_breakdown': dict(gender_breakdown),
        'barangay_breakdown': {k: dict(v) for k, v in barangay_breakdown.items()},
        'age_breakdown': {k: dict(v) for k, v in age_breakdown.items()},
    }
