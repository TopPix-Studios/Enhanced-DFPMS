from datetime import timedelta
from django.utils import timezone
from events.models import Event, Location, VirtualDetails
from profiling.models import Skills
import random

# Step 1: Create Locations
locations = [
    Location.objects.create(name="SM City General Santos", latitude=6.1164, longitude=125.1716),
    Location.objects.create(name="General Santos City Hall", latitude=6.1137, longitude=125.1711),
    Location.objects.create(name="KCC Mall of Gensan", latitude=6.1121, longitude=125.1713),
    Location.objects.create(name="Robinsons Place Gensan", latitude=6.1176, longitude=125.1709),
    Location.objects.create(name="Sarangani Highlands Garden", latitude=6.0985, longitude=125.1596),
]

# Step 2: Create Virtual Details
virtual_details = [
    VirtualDetails.objects.create(platform="Zoom", url="https://zoom.us/j/123456789", details="Meeting ID: 123456789"),
    VirtualDetails.objects.create(platform="Microsoft Teams", url="https://teams.microsoft.com/l/123", details="Access Code: TEAM123"),
    VirtualDetails.objects.create(platform="Google Meet", url="https://meet.google.com/xyz-abc-def", details="No Access Code Required"),
    VirtualDetails.objects.create(platform="Webex", url="https://webex.com/meet/456", details="Meeting ID: 456789"),
    VirtualDetails.objects.create(platform="Skype", url="https://join.skype.com/meeting", details="Guest Login Enabled"),
]

# Step 3: Create Tags/Skills
skill_1 = Skills.objects.create(skill="Networking")
skill_2 = Skills.objects.create(skill="Technology")
skill_3 = Skills.objects.create(skill="Leadership")
skill_4 = Skills.objects.create(skill="Innovation")

# Step 4: Create Only Past Events
def create_past_events():
    base_time = timezone.now()
    increment = timedelta(hours=2)

    descriptions = [
        "Explore the latest in AI and its real-world applications.",
        "Learn cloud computing essentials for startups.",
        "Workshop on leadership in tech-driven environments.",
        "Seminar on innovation strategies in the digital age.",
        "Introduction to cybersecurity for beginners.",
        "Future of remote work: tools and techniques.",
        "Data science crash course for decision-making.",
        "Smart city tech: shaping urban futures.",
        "Sustainable innovation and green technologies.",
        "Building robust tech communities locally.",
    ]

    for i in range(10):
        # All events start in the past (e.g., from 1 to 10 days ago)
        day_offset = -(i + 1)
        event_start = base_time + timedelta(days=day_offset)
        event_end = event_start + increment

        event = Event.objects.create(
            title=f"Past Tech Event #{i+1} in Gensan",
            description=descriptions[i % len(descriptions)],
            start_datetime=event_start,
            end_datetime=event_end,
            location_type="both" if i % 2 == 0 else "physical",
            location=locations[i % len(locations)],
            virtual_details=virtual_details[i % len(virtual_details)],
            organizer=f"Organizer {i+1}",
            is_published=True,
            is_cancelled=False,
            is_moved=False,
            remarks=f"This is a past event held on {event_start.strftime('%Y-%m-%d')}.",
            image=f"https://picsum.photos/seed/pastevent{i+1}/800/600"
        )

        if i % 2 == 0:
            event.tags.add(skill_1, skill_2)
        else:
            event.tags.add(skill_3, skill_4)

        print(f"Created Past Event: {event.title} - Start: {event_start.strftime('%Y-%m-%d %H:%M')}")

# Run it
create_past_events()
