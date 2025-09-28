from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.conf import settings
import pyotp
import uuid
import re
import qrcode
from io import BytesIO
from django.core.files import File
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from events.models import Event, Attendance
from support.models import SupportTicket
from geolocations.models import Region, Province, City, Barangay, Country
import logging


#Validators
def validate_phone_number(value):
    phone_regex = re.compile(
        r'^(?:\+639|09)\d{9}$|^(?:\+639|09)\d{2}-\d{3}-\d{4}$|^(?:\+639|09)\d{2}\s\d{3}\s\d{4}$'
    )
    if not phone_regex.match(value):
        raise ValidationError('Enter a valid Philippine contact number.', 'invalid')

#Models
class Role(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.CharField(max_length=255)

    def __str__(self):
        return self.role

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        # Your custom logic for creating a regular user
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        # Your custom logic for creating a superuser
        user = self.create_user(username, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user
    

class Account(AbstractBaseUser, PermissionsMixin):
    account_id = models.AutoField(
        primary_key=True,
        help_text="Unique identifier for the account."
    )
    username = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique username for the account."
    )
    email = models.EmailField(
        null=False,
        help_text="Email address associated with the account."
    )
    password = models.CharField(
        max_length=255,
        help_text="Secure password for the account."
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Indicates if the account has been verified."
    )
    verification_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        help_text="Token used for account verification."
    )
    join_date = models.DateTimeField(
        default=timezone.now,
        null=True,
        help_text="Date and time when the account was created."
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the account has staff privileges."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if the account is active."
    )
    otp_secret = models.CharField(
        max_length=32,
        default=pyotp.random_base32,
        blank=True,
        null=True,
        help_text="Secret key for generating one-time passwords."
    )
    last_login_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time of the last login."
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='user_accounts',
        help_text="Groups this account belongs to."
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='user_accounts',
        help_text="Specific permissions for this account."
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    def generate_otp(self):
        """Generate an OTP that’s valid for 10 minutes."""
        totp = pyotp.TOTP(self.otp_secret, interval=600)  # <-- 600s step
        return totp.now()

    def verify_otp(self, otp):
        """Verify the provided OTP against the secret key, valid for 10 min."""
        totp = pyotp.TOTP(self.otp_secret, interval=600)
        now = timezone.now()
        logging.debug(f"Expected OTP (10 min window): {totp.now()}")
        # No extra window needed, since interval itself is 10 min
        return totp.verify(otp)


class Affiliation(models.Model):
    aff_id = models.AutoField(
        primary_key=True,
        verbose_name='Affiliation ID',
        help_text="Unique identifier for the affiliation."
    )
    aff_name = models.CharField(
        max_length=255,
        verbose_name='Affiliation Name',
        help_text="Name of the affiliation or organization."
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Is Verified',
        help_text="Indicates whether the affiliation has been verified."
    )

    def __str__(self):
        return self.aff_name

    class Meta:
        verbose_name = 'Affiliation'
        verbose_name_plural = 'Affiliations'
        ordering = ['aff_name']  # Optional: Order by affiliation name



class PastExperience(models.Model):
    past_exp_id = models.AutoField(
        primary_key=True,
        verbose_name='Past Experience ID',
        help_text="Unique identifier for the past experience entry."
    )
    client = models.CharField(
        max_length=255,
        null=True,
        verbose_name='Client',
        help_text="Name of the client or company associated with this past experience."
    )
    country = models.ForeignKey(
        Country,  # Ensure 'Country' is defined elsewhere in your models
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Country',
        help_text="Country where the past experience took place."
    )
    year = models.DateField(
        null=True,
        verbose_name='Year',
        help_text="The year the experience occurred."
    )

    def __str__(self):
        return f"{self.client or 'Unknown Client'} - {self.country or 'Unknown Country'} - {self.year.year if self.year else 'Unknown Year'}"

    class Meta:
        verbose_name = 'Past Experience'
        verbose_name_plural = 'Past Experiences'
        ordering = ['-year']  # Order by year descending by default

class Specialization(models.Model):
    specialization_id = models.AutoField(
        primary_key=True,
        verbose_name='Specialization ID',
        help_text="Unique identifier for the specialization."
    )
    specialization = models.CharField(
        max_length=255,
        verbose_name='Specialization Name',
        help_text="Name of the specialization (e.g., Web Development, Data Science)."
    )
    description = models.CharField(
        max_length=255,
        verbose_name='Description',
        help_text="Brief description of the specialization."
    )

    def __str__(self):
        return self.specialization

    class Meta:
        verbose_name = 'Specialization'
        verbose_name_plural = 'Specializations'
        ordering = ['specialization']  # Optional: Order by specialization name alphabetically

class Language(models.Model):
    language_id = models.AutoField(
        primary_key=True,
        verbose_name='Language ID',
        help_text="Unique identifier for the language."
    )
    language = models.CharField(
        max_length=255,
        verbose_name='Language Name',
        help_text="Name of the language (e.g., English, Spanish, Mandarin)."
    )

    def __str__(self):
        return self.language

    class Meta:
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'
        ordering = ['language']  # Optional: Order by language name alphabetically


class Tag(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Tag Name',
        help_text="The name of the tag (e.g., Technology, Design, Business)."
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']  # Order tags alphabetically by name

class Skills(models.Model):
    skill_id = models.AutoField(
        primary_key=True,
        verbose_name="Skill ID",
        help_text="Unique identifier for the skill."
    )
    skill = models.CharField(
        max_length=255,
        verbose_name="Skill Name",
        help_text="Name of the skill (e.g., Python Development, SEO Optimization)."
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name="Related Tags",
        help_text="Tags associated with this skill for better categorization."
    )
    description = models.CharField(
        max_length=255,
        null=True,
        default="Customizing themes, managing extensions, and optimizing e-commerce websites for performance and usability.",
        verbose_name="Skill Description",
        help_text="A brief description of the skill."
    )

    def __str__(self):
        return self.skill

    class Meta:
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
        ordering = ["skill"]  # Optional: Orders skills alphabetically

class BackgroundInformationLanguage(models.Model):
    PROFICIENCY_LEVEL_CHOICES = [
        ('basic', 'Basic: Minimal understanding and communication'),
        ('conversational', 'Conversational: Can hold basic conversations'),
        ('fluent', 'Fluent: Comfortable in most situations'),
        ('native', 'Native: Complete mastery of the language'),
    ]

    background_information = models.ForeignKey(
        'BackgroundInformation',
        on_delete=models.CASCADE,
        verbose_name="Background Information",
        help_text="The background information associated with this language proficiency."
    )
    language = models.ForeignKey(
        'Language',
        on_delete=models.CASCADE,
        verbose_name="Language",
        help_text="The language for which proficiency is specified."
    )
    proficiency_level = models.CharField(
        max_length=15,
        choices=PROFICIENCY_LEVEL_CHOICES,
        default='basic',
        verbose_name="Proficiency Level",
        help_text="Level of proficiency in the selected language."
    )

    def __str__(self):
        return f"{self.language} ({self.get_proficiency_level_display()})"

    def get_proficiency_description(self):
        """
        Extract and return the detailed description of the proficiency level.
        """
        description = dict(self.PROFICIENCY_LEVEL_CHOICES).get(self.proficiency_level, '')
        return description.split(':', 1)[1].strip() if ':' in description else description

    class Meta:
        verbose_name = "Background Information Language"
        verbose_name_plural = "Background Information Languages"
        ordering = ["language"]


class BackgroundInformation(models.Model):
    bg_id = models.AutoField(
        primary_key=True,
        verbose_name="Background Information ID",
        help_text="Unique identifier for the background information entry."
    )
    affiliation = models.ForeignKey(
        'Affiliation',
        on_delete=models.CASCADE,
        verbose_name="Affiliation",
        help_text="The affiliation or organization associated with this background information."
    )
    past_experiences = models.ManyToManyField(
        'PastExperience',
        verbose_name="Past Experiences",
        help_text="Past experiences associated with this background information."
    )
    specialization = models.ForeignKey(
        'Specialization',
        on_delete=models.CASCADE,
        related_name='background_information_specializations',
        verbose_name="Specialization",
        help_text="The specialization associated with this background information."
    )
    language = models.ManyToManyField(
        'Language',
        through='BackgroundInformationLanguage',
        verbose_name="Languages",
        help_text="Languages and their proficiency levels associated with this background information."
    )
    skills = models.ManyToManyField(
        'Skills',
        verbose_name="Skills",
        help_text="Skills associated with this background information."
    )

    def __str__(self):
        return f"Affiliation: {self.affiliation}, Specialization: {self.specialization.specialization}"

    class Meta:
        verbose_name = "Background Information"
        verbose_name_plural = "Background Information"
        ordering = ["affiliation"]


class Profile(models.Model):
    df_id = models.AutoField(
        primary_key=True,
        verbose_name="Profile ID",
        help_text="Unique identifier for the profile."
    )
    first_name = models.CharField(
        max_length=255,
        verbose_name="First Name",
        help_text="The first name of the profile owner."
    )
    last_name = models.CharField(
        max_length=255,
        verbose_name="Last Name",
        help_text="The last name of the profile owner."
    )
    suffix = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Suffix",
        help_text="Suffix for the name (e.g., Jr., Sr., III)."
    )
    middle_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Middle Name",
        help_text="The middle name of the profile owner."
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        verbose_name="Region",
        help_text="Region of the profile owner."
    )
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        verbose_name="Province",
        help_text="Province of the profile owner."
    )
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        verbose_name="City",
        help_text="City of the profile owner."
    )
    barangay = models.ForeignKey(
        Barangay,
        on_delete=models.CASCADE,
        verbose_name="Barangay",
        help_text="Barangay of the profile owner."
    )
    zip = models.CharField(
        max_length=255,
        verbose_name="ZIP Code",
        help_text="ZIP code of the profile owner's address."
    )
    house_no = models.CharField(
        max_length=255,
        verbose_name="House Number",
        help_text="House number of the profile owner's address."
    )
    street = models.CharField(
        max_length=255,
        verbose_name="Street",
        help_text="Street name of the profile owner's address."
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date of Birth",
        help_text="The date of birth of the profile owner."
    )
    contact_no = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        validators=[validate_phone_number],
        verbose_name="Contact Number",
        help_text="The contact number of the profile owner (e.g., +123456789)."
    )
    gender = models.CharField(
        max_length=255,
        verbose_name="Gender",
        help_text="Gender of the profile owner (e.g., Male, Female, Non-binary)."
    )
    picture = models.ImageField(
        upload_to='profile/',
        null=True,
        blank=True,
        verbose_name="Profile Picture",
        help_text="Profile picture of the user."
    )
    account_id = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        verbose_name="Account",
        help_text="Account associated with this profile."
    )
    bg_id = models.ForeignKey(
        'BackgroundInformation',
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Background Information",
        help_text="Background information associated with this profile."
    )
    qoute = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default="Having people acknowledge your existence is a wonderful thing.",
        verbose_name="Quote",
        help_text="A favorite quote of the profile owner."
    )
    pronoun = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        default="he/she",
        verbose_name="Preferred Pronoun",
        help_text="Preferred pronoun of the profile owner (e.g., he/she, they/them)."
    )
    is_pwd = models.BooleanField(
        default=False,
        verbose_name="Is PWD",
        help_text="Indicates if the profile owner is a Person with Disability (PWD)."
    )
    is_4ps = models.BooleanField(
        default=False,
        verbose_name="Is 4Ps Beneficiary",
        help_text="Indicates if the profile owner is a 4Ps beneficiary."
    )

    is_archived = models.BooleanField(
        default=False,
        verbose_name="Is Archived",
        help_text="Mark this profile as archived."
    )


    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["last_name", "first_name"]




class Resume(models.Model):
    profile = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Profile",
        help_text="The profile associated with this resume."
    )
    resume_file = models.FileField(
        upload_to='resumes/',
        verbose_name="Resume File",
        help_text="Upload the resume file (PDF, DOCX, etc.)."
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Uploaded At",
        help_text="The date and time when the resume was uploaded."
    )

    def __str__(self):
        return f"Resume for {self.profile.first_name} {self.profile.last_name} ({self.profile.df_id})"

    class Meta:
        verbose_name = "Resume"
        verbose_name_plural = "Resumes"
        ordering = ["-uploaded_at"]  # Order by most recent upload

class Project(models.Model):
    profile = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Profile",
        help_text="The profile associated with this project."
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Project Title",
        help_text="The title of the project."
    )
    description = models.TextField(
        verbose_name="Project Description",
        help_text="A detailed description of the project."
    )
    pdf_file = models.FileField(
        upload_to='projects/',
        verbose_name="Project File (PDF)",
        help_text="Upload the project file in PDF format."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="The date and time when the project was created."
    )

    def __str__(self):
        if self.profile:
            profile_name = f"{self.profile.first_name} {self.profile.last_name}"
        else:
            profile_name = "No Profile"
        return f"{self.title} (Profile: {profile_name})"

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-created_at"]  # Display projects by most recent creation date
    

class Certificate(models.Model):
    CATEGORY_CHOICES = [
        ('Customer Acquisition Specialist', 'Customer Acquisition Specialist'),
        ('Analytics & Data Specialist', 'Analytics & Data Specialist'),
        ('Optimization & Testing Specialist', 'Optimization & Testing Specialist'),
        ('Search Marketing Specialist', 'Search Marketing Specialist'),
        ('Email Marketing Specialist', 'Email Marketing Specialist'),
        ('Others', 'Others'),
    ]

    profile = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Profile",
        help_text="The profile associated with this certificate."
    )
    certificate_title = models.CharField(
        max_length=255,
        verbose_name="Certificate Title",
        help_text="The title of the certificate."
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="An optional description of the certificate."
    )
    issued_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Issued By",
        help_text="The organization or authority that issued the certificate."
    )
    date_issued = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date Issued",
        help_text="The date the certificate was issued."
    )
    image_file = models.ImageField(
        upload_to='certificates/',
        verbose_name="Certificate Image",
        help_text="An optional image of the certificate."
    )
    category = models.CharField(
        max_length=255,
        choices=CATEGORY_CHOICES,
        default='Others',
        verbose_name="Category",
        help_text="The category of the certificate."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="The date and time when the certificate was added."
    )

    def get_badge_image(self):
        """
        Returns the badge image URL associated with the certificate's category.
        """
        badge_mapping = {
            'Customer Acquisition Specialist': 'img/Badges/Purple.png',
            'Analytics & Data Specialist': 'img/Badges/Red.png',
            'Optimization & Testing Specialist': 'img/Badges/Yellow.png',
            'Search Marketing Specialist': 'img/Badges/Green.png',
            'Email Marketing Specialist': 'img/Badges/Orange.png',
            'Others': 'img/Badges/Yellow.png',
        }
        return badge_mapping.get(self.category, '/img/Badges/Yellow.png')

    def __str__(self):
        return f"{self.certificate_title} ({self.category})"

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"
        ordering = ["-created_at"]  # Show most recently created certificates first


class ProjectTag(models.Model):
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        verbose_name="Project",
        help_text="The project associated with this tag."
    )
    tag = models.ForeignKey(
        'Tag',
        on_delete=models.CASCADE,
        verbose_name="Tag",
        help_text="The tag associated with this project."
    )

    def __str__(self):
        return f"{self.project.title} - {self.tag.name}"

    class Meta:
        verbose_name = "Project Tag"
        verbose_name_plural = "Project Tags"
        unique_together = ('project', 'tag')  # Ensure that a project and tag pair is unique


class Log(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('access', 'Access'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="User",
        help_text="The user who performed the action. Null if anonymous."
    )
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
        verbose_name="Action",
        help_text="The type of action logged (e.g., Create, Update, Delete, Access)."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Timestamp",
        help_text="The date and time when the action was logged."
    )
    url = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="URL",
        help_text="The URL associated with the logged action."
    )
    view_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="View Name",
        help_text="The name of the Django view accessed, if applicable."
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Content Type",
        help_text="The type of content associated with the action (if any)."
    )
    object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Object ID",
        help_text="The ID of the object associated with the action (if any)."
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    message = models.TextField(
        verbose_name="Message",
        help_text="Additional details or context about the action."
    )

    def __str__(self):
        return f"{self.action.capitalize()} - {self.url or 'No URL'} by {self.user or 'Anonymous'}"

    class Meta:
        verbose_name = "Log Entry"
        verbose_name_plural = "Log Entries"
        ordering = ["-timestamp"]  # Show the most recent logs first

