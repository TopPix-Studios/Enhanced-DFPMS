import os
import random
from django.core.files import File
from django.utils import timezone
from django.conf import settings
from events.models import Announcement
from profiling.models import Skills
from django.contrib.auth import get_user_model

# Step 1: Get or Create an Author
User = get_user_model()
author, created = User.objects.get_or_create(username="seanne-admin", defaults={"password": "123"})

# Step 2: Generate Dummy Announcements
def create_dummy_announcements():
    # Path to the static image file
    static_image_path = os.path.join(settings.BASE_DIR, "static", "img","DarkBlue", "dark blue.png")

    # Check if the static image exists
    if not os.path.exists(static_image_path):
        print("Error: Static image not found at:", static_image_path)
        return

    # Fetch all existing skills
    all_skills = list(Skills.objects.all())
    if not all_skills:
        print("Error: No skills found in the database. Add skills before running this script.")
        return

    # Generate 10 dummy announcements
    for i in range(1, 11):
        announcement = Announcement.objects.create(
            title=f"Important Announcement #{i}",
            content=f"This is the content for Important Announcement #{i}. Stay informed about updates in General Santos City.",
            address="General Santos City",
            latitude=6.1164,
            longitude=125.1716,
            created_at=timezone.now(),
            author=author
        )

        # Assign random skills (1 to 3 skills per announcement)
        selected_skills = random.sample(all_skills, random.randint(1, 3))
        for skill in selected_skills:
            announcement.tags.add(skill)

        # Assign the static image as the announcement image
        with open(static_image_path, "rb") as img_file:
            announcement.image.save(f"announcement_{i}.png", File(img_file), save=True)

        print(f"Created Announcement: {announcement.title}, Skills: {[skill.skill for skill in selected_skills]}")

# Run the function
create_dummy_announcements()
