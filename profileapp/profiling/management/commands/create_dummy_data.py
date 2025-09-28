import random
from faker import Faker
import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from profiling.models import (
    Account, Profile, BackgroundInformation, Project, Resume,
    PastExperience, Affiliation, Specialization, Language, Skills
)
from geolocations.models import Country, Region, Province, City, Barangay
from events.models import Event, Attendance, RSVP, Announcement
from django.utils import timezone
import string

fake = Faker()

class Command(BaseCommand):
    help = 'Generate dummy data for Account, Profile, BackgroundInformation, Project, Resume, and populate Attendance and RSVP models for existing Events'

    def handle(self, *args, **kwargs):
        # Fetch specific region, province, city, and related barangays
        try:
            region = Region.objects.get(region_id=15)
            province = Province.objects.get(province_id=3, region=region)
            city = City.objects.get(city_id=27, province=province)
            barangays = list(Barangay.objects.filter(city=city))
        except (Region.DoesNotExist, Province.DoesNotExist, City.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(f"{str(e)}"))
            return

        # Check if there are barangays available for the specified city
        if not barangays:
            self.stdout.write(self.style.ERROR('No barangays found for city_id=27'))
            return

        affiliations = list(Affiliation.objects.all())
        specializations = list(Specialization.objects.all())
        languages = list(Language.objects.all())
        skills = list(Skills.objects.all())

        # # Fetch existing events and announcements
        events = list(Event.objects.all())
        if not events:
            self.stdout.write(self.style.WARNING('No existing events found. Cannot populate Attendance or RSVP data.'))
            return

        # announcements = list(Announcement.objects.all())
        # if not announcements:
        #     self.stdout.write(self.style.WARNING('No existing announcements found.'))

        for _ in range(1000):
            # Create an Account
            # Generate a more complex username
            username = f"{fake.word()}_{fake.word()}{random.randint(10, 999)}{random.choice(string.punctuation)}"

            account = Account.objects.create_user(
                username=username,
                email=fake.email(),
                password='Password123'
            )

            # Create Background Information
            background = BackgroundInformation.objects.create(
                affiliation=random.choice(affiliations) if affiliations else None,
                specialization=random.choice(specializations) if specializations else None
            )
            background.language.set(random.sample(languages, min(3, len(languages))))
            background.skills.set(random.sample(skills, min(5, len(skills))))

            # Create Past Experiences for BackgroundInformation
            past_experiences = [
                PastExperience.objects.create(
                    client=fake.company(),
                    country=Country.objects.order_by('?').first(),
                    year=fake.date_this_century()
                )
                for _ in range(random.randint(1, 5))
            ]
            background.past_experiences.set(past_experiences)

            # Create Profile with the specific barangay
            profile = Profile.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                suffix=fake.suffix()[:15],
                middle_name=fake.first_name(),
                region=region,
                province=province,
                city=city,
                barangay=random.choice(barangays),  # Random barangay in city_id=27
                zip=fake.zipcode()[:10],
                house_no=fake.building_number(),
                street=fake.street_name(),
                date_of_birth=fake.date_of_birth(),
                contact_no=self.generate_valid_phone_number(),
                gender=random.choice(['male', 'female']),
                account_id=account,
                qoute=fake.sentence(),
                bg_id=background
            )

            # Create a Project associated with Profile
            Project.objects.create(
                title=fake.catch_phrase(),
                description=fake.text(),
                pdf_file=f"projects/{fake.file_name(extension='pdf')}",
                profile=profile
            )

            # Create a Resume associated with Profile
            Resume.objects.create(
                resume_file=f"resumes/{fake.file_name(extension='pdf')}",
                profile=profile
            )

            # Inside the for loop after creating profile and resume/project

            event = random.choice(events)  # Pick a random event
            now = timezone.now()

            # RSVP only for future events
            if event.start_datetime > now and random.random() < 0.7:
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

            # Attendance only for past or present events
            if event.start_datetime <= now and random.random() < 0.5:
                Attendance.objects.create(
                    event=event,
                    user=account,
                    name=f"{profile.first_name} {profile.last_name}",
                    age_range=random.choice(['A', 'B', 'C', 'D', 'E']),
                    gender=random.choice(['M', 'F', 'O']),
                    pwd=random.choice([True, False]),
                    four_ps=random.choice([True, False]),
                    affiliation=random.choice(affiliations).aff_name if affiliations else "",
                    contact=profile.contact_no,
                    email=account.email,
                    date=timezone.now(),
                    logged_in=random.choice([True])
                )


        self.stdout.write(self.style.SUCCESS('Successfully generated dummy data for Account, Profile, BackgroundInformation, Project, Resume, and populated Attendance and RSVP models for existing Events'))

    def generate_valid_phone_number(self):
        return f"09{random.randint(100000000, 999999999)}"
