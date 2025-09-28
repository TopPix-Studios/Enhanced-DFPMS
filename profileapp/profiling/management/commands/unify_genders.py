from django.core.management.base import BaseCommand
from profiling.models import Profile

GENDER_MAPPING = {
    'male': 'male',
    'm': 'male',
    'female': 'female',
    'f': 'female',
    'other': 'other',
    'prefer not to say': 'prefer not to say',
    'prefer not to disclose': 'prefer not to say',
    'n/a': 'prefer not to say',
    'none': 'prefer not to say',
}

class Command(BaseCommand):
    help = 'Standardizes gender field in Profile model.'

    def handle(self, *args, **kwargs):
        profiles = Profile.objects.exclude(gender__isnull=True).exclude(gender__exact='')

        updated_count = 0
        for profile in profiles:
            original_gender = profile.gender.strip().lower()
            standardized_gender = GENDER_MAPPING.get(original_gender)
            if standardized_gender and profile.gender != standardized_gender:
                profile.gender = standardized_gender
                profile.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully standardized {updated_count} profiles.'))
