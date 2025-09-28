from django.db import models
import qrcode
from django.utils import timezone
from django.conf import settings
from io import BytesIO
from django.core.files import File
from django.urls import reverse
from django.core.exceptions import ValidationError


class Attendance(models.Model):
    AGE_RANGES = [
        ('A', '20 below'),
        ('B', '20-29'),
        ('C', '30-39'),
        ('D', '40-49'),
        ('E', '50+'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="Event",
        help_text="The event for which attendance is recorded."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="User",
        help_text="The user associated with this attendance (if logged in)."
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Attendee Name",
        help_text="The name of the attendee."
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name="Attendance Date",
        help_text="The date the attendee was recorded."
    )
    logged_in = models.BooleanField(
        default=False,
        verbose_name="Logged In",
        help_text="Indicates if the attendee logged in using an account."
    )
    age_range = models.CharField(
        max_length=7,
        choices=AGE_RANGES,
        null=True,
        default=None,
        verbose_name="Age Range",
        help_text="The age range of the attendee."
    )
    gender = models.CharField(
        max_length=6,
        choices=GENDER_CHOICES,
        null=True,
        default=None,
        verbose_name="Gender",
        help_text="The gender of the attendee."
    )
    pwd = models.BooleanField(
        default=False,
        verbose_name="Person with Disability (PWD)",
        help_text="Indicates if the attendee is a Person with Disability (PWD)."
    )
    four_ps = models.BooleanField(
        default=False,
        verbose_name="4Ps Beneficiary",
        help_text="Indicates if the attendee is a 4Ps beneficiary."
    )
    affiliation = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Affiliation",
        help_text="The affiliation or organization of the attendee."
    )
    contact = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Contact Number",
        help_text="The contact number of the attendee."
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name="Email",
        help_text="The email address of the attendee."
    )

    def __str__(self):
        return f'{self.name} attending {self.event.title} on {self.date}'

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"
        ordering = ["-date", "event"]

class Location(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Location Name",
        help_text="The name of the location (e.g., City, Park, or Landmark)."
    )
    latitude = models.FloatField(
        default=6.1164,
        null=True,
        blank=True,
        verbose_name="Latitude",
        help_text="Latitude coordinate of the location."
    )
    longitude = models.FloatField(
        default=125.1716,
        null=True,
        blank=True,
        verbose_name="Longitude",
        help_text="Longitude coordinate of the location."
    )

    def __str__(self):
        return self.name

    def coordinates(self):
        """
        Returns the coordinates as a tuple (latitude, longitude).
        """
        return (self.latitude, self.longitude)

    def google_maps_link(self):
        """
        Returns a Google Maps link for the location.
        """
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        ordering = ["name"]  # Alphabetical order by location name


class VirtualDetails(models.Model):
    platform = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Platform",
        help_text="The platform used for the virtual event (e.g., Zoom, Google Meet)."
    )
    url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Meeting URL",
        help_text="The URL link to join the virtual event."
    )
    details = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Additional Details",
        help_text="Optional additional details about the virtual event."
    )

    def __str__(self):
        return self.platform or "Virtual Event"

    def is_complete(self):
        """
        Checks if all necessary details for a virtual event are provided.
        """
        return bool(self.platform and self.url)

    def get_meeting_link(self):
        """
        Returns the URL of the virtual meeting if available.
        """
        return self.url or "No meeting link provided."

    class Meta:
        verbose_name = "Virtual Details"
        verbose_name_plural = "Virtual Details"
        ordering = ["platform"]  # Orders by platform name alphabetically
    

class RSVP(models.Model):
    RSVP_STATUS_CHOICES = [
        ('interested', 'Interested'),
        ('attending', 'Attending'),
        ('not_attending', 'Not Attending'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rsvps',
        verbose_name="User",
        help_text="The user responding to the event."
    )
    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='rsvps',
        verbose_name="Event",
        help_text="The event the user is responding to."
    )
    status = models.CharField(
        max_length=15,
        choices=RSVP_STATUS_CHOICES,
        default='interested',
        verbose_name="RSVP Status",
        help_text="The RSVP status of the user for this event."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Timestamp",
        help_text="The date and time when the RSVP was made."
    )

    class Meta:
        unique_together = ('user', 'event')  # Ensure a user can RSVP only once per event
        verbose_name = "RSVP"
        verbose_name_plural = "RSVPs"
        ordering = ['-timestamp']  # Show the most recent RSVPs first

    def __str__(self):
        return f"{self.user} - {self.event} ({self.get_status_display()})"

    def is_attending(self):
        """
        Check if the user is marked as attending.
        """
        return self.status == 'attending'

    def is_interested(self):
        """
        Check if the user is marked as interested.
        """
        return self.status == 'interested'

    def is_not_attending(self):
        """
        Check if the user is marked as not attending.
        """
        return self.status == 'not_attending'
    
class Event(models.Model):
    LOCATION_TYPE_CHOICES = [
        ('physical', 'Physical'),
        ('virtual', 'Virtual'),
        ('both', 'Both')
    ]

    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="The title of the event."
    )
    description = models.TextField(
        verbose_name="Description",
        help_text="A detailed description of the event."
    )
    start_datetime = models.DateTimeField(
        verbose_name="Start Date and Time",
        help_text="The start date and time of the event."
    )
    end_datetime = models.DateTimeField(
        verbose_name="End Date and Time",
        help_text="The end date and time of the event."
    )
    location_type = models.CharField(
        max_length=10,
        choices=LOCATION_TYPE_CHOICES,
        default='physical',
        verbose_name="Location Type",
        help_text="Indicates if the event is physical, virtual, or both."
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Location",
        help_text="The physical location of the event."
    )
    virtual_details = models.ForeignKey(
        'VirtualDetails',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Virtual Details",
        help_text="Details for joining the virtual event."
    )
    organizer = models.CharField(
        max_length=255,
        verbose_name="Organizer",
        help_text="The organizer of the event."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="The date and time when the event was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
        help_text="The date and time when the event was last updated."
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name="Is Published",
        help_text="Indicates if the event is published."
    )
    is_cancelled = models.BooleanField(
        default=False,
        verbose_name="Is Cancelled",
        help_text="Indicates if the event is cancelled."
    )
    is_moved = models.BooleanField(
        default=False,
        verbose_name="Is Moved",
        help_text="Indicates if the event has been moved."
    )
    remarks = models.TextField(
        blank=True,
        null=True,
        verbose_name="Remarks",
        help_text="Additional remarks about the event."
    )
    tags = models.ManyToManyField(
        'profiling.Skills',
        related_name='events',
        verbose_name="Tags",
        help_text="Skills or categories associated with the event."
    )
    image = models.ImageField(
        upload_to='events/',
        null=True,
        blank=True,
        verbose_name="Event Image",
        help_text="Optional image representing the event."
    )
    qr_code = models.ImageField(
        upload_to='events/qr_codes/',
        null=True,
        blank=True,
        verbose_name="QR Code",
        help_text="QR code for the event URL."
    )

    def __str__(self):
        return self.title

    def is_virtual(self):
        return self.location_type in ['virtual', 'both']

    def is_physical(self):
        return self.location_type in ['physical', 'both']

    def get_attendees(self):
        return self.rsvps.filter(status='attending')

    def get_interested_users(self):
        return self.rsvps.filter(status='interested')

    def get_not_attending_users(self):
        return self.rsvps.filter(status='not_attending')

    def generate_qr_code(self, request):
        """
        Generates a QR code for the event and saves it to the qr_code field.
        """
        if not request:
            raise ValueError("Request object is required to generate QR code.")
        
        # Build the event URL using request to get the full absolute URL
        event_url = reverse('guest_event', args=[self.id])
        full_url = request.build_absolute_uri(event_url)

        # Generate the QR code
        qr = qrcode.make(full_url)
        buffer = BytesIO()
        qr.save(buffer)
        buffer.seek(0)

        # Save the QR code image to the event's qr_code field
        file_name = f'{self.title}_qr.png'
        self.qr_code.save(file_name, File(buffer), save=False)

    def save(self, *args, **kwargs):
        # Validate the event dates
        self.full_clean()
        
        # Save the event
        request = kwargs.pop('request', None)
        super().save(*args, **kwargs)  # Save the event first to generate the ID

        # Generate QR code if a request is provided
        if request:
            self.generate_qr_code(request)
            super().save(update_fields=['qr_code'])  # Save only the QR code field

    def clean(self):
        """
        Custom validation to ensure end_datetime is after start_datetime.
        """
        if self.end_datetime <= self.start_datetime:
            raise ValidationError("End date and time must be after start date and time.")

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['-created_at']  # Show the most recently created events first

class Announcement(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="Title",
        help_text="The title of the announcement."
    )
    content = models.TextField(
        verbose_name="Content",
        help_text="The content or details of the announcement."
    )
    address = models.TextField(
        default="General Santos City",
        null=True,
        blank=True,
        verbose_name="Address",
        help_text="Address related to the announcement. Leave blank if no specific location is needed."
    )
    latitude = models.FloatField(
        default=6.1164,
        null=True,
        blank=True,
        verbose_name="Latitude",
        help_text="Latitude of the announcement's location. Defaults to General Santos City."
    )
    longitude = models.FloatField(
        default=125.1716,
        null=True,
        blank=True,
        verbose_name="Longitude",
        help_text="Longitude of the announcement's location. Defaults to General Santos City."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="The date and time when the announcement was created."
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcements',
        verbose_name="Author",
        help_text="The user who created the announcement."
    )
    tags = models.ManyToManyField(
        'profiling.Skills',
        related_name='announcements',
        verbose_name="Tags",
        help_text="Skills or categories associated with the announcement."
    )
    image = models.ImageField(
        upload_to='announcements/',
        null=True,
        blank=True,
        verbose_name="Image",
        help_text="Optional image related to the announcement."
    )

    def __str__(self):
        return self.title

    def get_location_coordinates(self):
        """
        Returns the latitude and longitude as a tuple.
        """
        return (self.latitude, self.longitude)

    def google_maps_link(self):
        """
        Returns a Google Maps link for the announcement's location.
        """
        if self.latitude is not None and self.longitude is not None:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return "No location coordinates available."

    class Meta:
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"
        ordering = ["-created_at"]  # Most recent announcements appear first