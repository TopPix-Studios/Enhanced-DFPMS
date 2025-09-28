from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event, RSVP
from profiling.models import Account
import random

class Command(BaseCommand):
    help = 'Generate RSVP records for past events only with weighted status'

    def handle(self, *args, **kwargs):
        past_events = list(Event.objects.filter(start_datetime__lt=timezone.now(), is_published=True))
        accounts = list(Account.objects.all())

        if not past_events:
            self.stdout.write(self.style.WARNING('No past events found.'))
            return

        if not accounts:
            self.stdout.write(self.style.WARNING('No accounts available to assign RSVPs.'))
            return

        count = 0
        for account in accounts:
            selected_events = random.sample(past_events, min(len(past_events), random.randint(1, 5)))
            for event in selected_events:
                if not RSVP.objects.filter(user=account, event=event).exists():
                    status = random.choices(
                        ['attending', 'interested', 'not_attending'],
                        weights=[80, 15, 5],
                        k=1
                    )[0]
                    RSVP.objects.create(
                        user=account,
                        event=event,
                        status=status
                    )
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully generated {count} RSVP records for past events.'))
