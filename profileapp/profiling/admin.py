from django.contrib import admin
from .models import Account, Tag, Event, Project, Profile, Attendance, Language, Affiliation, Region, Province, City, Barangay, Skills, Specialization, PastExperience, BackgroundInformation, Resume, Certificate
from django.http import HttpResponse
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from django.template.response import TemplateResponse
from io import BytesIO
from xhtml2pdf import pisa
from django.urls import path
from django.contrib.admin import AdminSite
from django.utils.safestring import mark_safe
from .admin_forms import AccountAdminForm
import qrcode   
import csv
from django.urls import reverse
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from allauth.account.models import EmailAddress
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.shortcuts import render,  redirect, get_object_or_404
from django.utils import timezone
from django.core.files.base import ContentFile
from .utils import send_profile_incomplete_email  # if defined elsewhere
from .utils import generate_secure_edit_link, send_profile_missing_email
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from rangefilter.filters import DateRangeFilter



# admin.site.unregister(Site)
admin.site.unregister(EmailAddress)
# admin.site.unregister(SocialAccount)
# admin.site.unregister(SocialApp)
# admin.site.unregister(SocialToken)
admin.site.unregister(Group)



def export_to_csv(modeladmin, request, queryset):
    meta = modeladmin.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={meta}.csv'
    writer = csv.writer(response)

    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])

    return response

export_to_csv.short_description = "Export Selected to CSV"



# Affiliation Admin
def verify_affiliations(modeladmin, request, queryset):
    queryset.update(is_verified=True)

verify_affiliations.short_description = "Mark selected affiliations as verified"

class AffiliationAdmin(admin.ModelAdmin):
    list_display = ('aff_id', 'aff_name', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('aff_name',)
    ordering = ('aff_id',)
    actions = [verify_affiliations, export_to_csv]

admin.site.register(Affiliation, AffiliationAdmin)



# Language Admin
class LanguageAdmin(admin.ModelAdmin):
    change_list_template = "admin/language_change_list.html"
    actions = [export_to_csv]
    
    search_fields = ['language']
    list_filter = ['language']
    list_display = ['language_id', 'language']

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['language_chart_url'] = '/admin/language-chart/'
        return super(LanguageAdmin, self).changelist_view(request, extra_context=extra_context)

admin.site.register(Language, LanguageAdmin)

# class AttendanceAdmin(admin.ModelAdmin):
#     list_display = ('name', 'event', 'user', 'logged_in', 'age_range', 'gender', 'pwd', 'four_ps', 'affiliation', 'contact', 'email')
#     list_filter = ('event', 'logged_in', 'age_range', 'gender', 'pwd', 'four_ps')
#     search_fields = ('name', 'event__title', 'user__username', 'affiliation', 'contact', 'email')
#     readonly_fields = ('name', 'event', 'user', 'age_range', 'gender')

# admin.site.register(Attendance, AttendanceAdmin)

class SkillsTagInline(admin.TabularInline):
    model = Skills.tags.through
    extra = 0

class SkillsAdmin(admin.ModelAdmin):
    change_list_template = "admin/skills_change_list.html"
    list_filter = ['tags']
    search_fields = ['skill', 'tags__name']

    actions = [export_to_csv]

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['skills_chart_url'] = '/admin/skills-chart/'
        return super(SkillsAdmin, self).changelist_view(request, extra_context=extra_context)

    def tags_display(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())

    tags_display.short_description = 'Main Skill'

    inlines = [SkillsTagInline]

    list_display = ['skill', 'description', 'tags_display']

admin.site.register(Skills, SkillsAdmin)

class TagAdmin(admin.ModelAdmin):
    inlines = [SkillsTagInline]

    def related_skills(self, obj):
        skills = Skills.objects.filter(tags=obj)
        return ", ".join([skill.skill for skill in skills])

    related_skills.short_description = "Related Skills"

    list_display = ['name', 'related_skills']

admin.site.register(Tag, TagAdmin)



# Specialization Admin
class SpecializationAdmin(admin.ModelAdmin):
    change_list_template = "admin/specialization_change_list.html"
    actions = [export_to_csv]

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['specialization_chart_url'] = '/admin/specialization-chart/'
        return super(SpecializationAdmin, self).changelist_view(request, extra_context=extra_context)

admin.site.register(Specialization, SpecializationAdmin)


def past_exp_export_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report.csv"'
    writer = csv.writer(response)
    # Write headers
    writer.writerow(['Client', 'Country', 'Year'])
    # Write data
    for obj in queryset:
        writer.writerow([obj.client, obj.country.country if obj.country else '', obj.year])
    return response

past_exp_export_as_csv.short_description = "Export selected objects as CSV file"

def verify_accounts(modeladmin, request, queryset):
    current_site = Site.objects.get_current()
    base_url = f"{current_site.domain}"
    login_link = f"{base_url}{reverse('user_login')}"

    for account in queryset:
        if not account.is_verified:
            account.is_verified = True
            account.save()

            try:
                # Prepare email context
                context = {
                    'user': account,
                    'site_name': 'Digital Freelancer Profiling System',
                    'login_link': login_link,
                }

                # Render email content
                html_content = render_to_string("emails/verified_account_email.html", context)
                plain_content = strip_tags(html_content)

                # Send email
                email = EmailMultiAlternatives(
                    subject="Your Account Has Been Verified",
                    body=plain_content,
                    from_email="gensanity.information@gmail.com",
                    to=[account.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()

                messages.success(request, f"Verification email sent to {account.email}.")

            except Exception as e:
                messages.error(request, f"Failed to send email to {account.username}: {e}")

verify_accounts.short_description = "Mark selected accounts as verified"


def activate_account(modeladmin, request, queryset):
    for account in queryset:
        if not account.is_active:
            account.is_active = True
            account.save()

activate_account.short_description = "Mark selected accounts as active"

def deactivate_account(modeladmin, request, queryset):
    for account in queryset:
        if account.is_active:
            account.is_active = False
            account.save()

deactivate_account.short_description = "Mark selected accounts as inactive"


def notify_incomplete_profiles(modeladmin, request, queryset):
    notified_count = 0
    for account in queryset:
        try:
            profile = Profile.objects.get(account_id=account)
            missing_items = []

            if not profile.resume:
                missing_items.append('resume')
            if not profile.portfolio:
                missing_items.append('portfolio')

            if missing_items:
                edit_link_base = f"{settings.SITE_URL}{reverse('edit_resume_projects', args=[profile.df_id])}"
                send_profile_incomplete_email(account, missing_items, edit_link_base)
                notified_count += 1
        except Profile.DoesNotExist:
            continue

    messages.success(request, f"✅ {notified_count} user(s) notified about missing profile items.")


def reject_and_delete_accounts(modeladmin, request, queryset):
    for account in queryset:
        try:
            # Prepare email context
            context = {
                'user': account,
                'site_title': "DF Profiling System",
                'site_name': "Digital Freelancer Profiling System",
            }

            # Render HTML and plain text versions
            html_content = render_to_string("emails/rejection_email.html", context)
            plain_content = strip_tags(html_content)

            # Compose and send email
            subject = "Registration Rejected - DF Profiling System"
            from_email = "gensanity.information@gmail.com"  # Update with your sender email
            to_email = account.email

            email = EmailMultiAlternatives(subject, plain_content, from_email, [to_email])
            email.attach_alternative(html_content, "text/html")
            email.send()

            # Delete account after sending the email
            account.delete()

        except Exception as e:
            messages.error(request, f"Error processing {account.username}: {str(e)}")
            continue

    messages.success(request, "Selected account(s) have been notified and deleted.")

reject_and_delete_accounts.short_description = "Reject and delete selected accounts"

class AccountAdmin(admin.ModelAdmin):
    form = AccountAdminForm

    list_display = ('username', 'email', 'is_verified', 'join_date', 'last_login', 'view_profile_link', 'notify_link')
    list_filter = ('is_verified', 'join_date')
    search_fields = ('username', 'email')
    actions = [verify_accounts, export_to_csv, deactivate_account, activate_account, reject_and_delete_accounts]

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_verified')}),
        ('Important dates', {'fields': ('last_login', 'join_date')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'is_verified', 'join_date', 'is_staff', 'is_active')}
        ),
    )

    def view_profile_link(self, obj):
        try:
            profile = Profile.objects.get(account_id=obj)
            url = reverse("admin_profile_detail", args=[profile.df_id])
            return format_html('<a href="{}">View Profile</a>', url)
        except Profile.DoesNotExist:
            return format_html('<span style="color: #999;">No Profile</span>')

    view_profile_link.short_description = "Profile"
    view_profile_link.admin_order_field = 'profile__df_id'

    def notify_link(self, obj):
        url = reverse('admin:notify_missing_profile', args=[obj.pk])
        return format_html('<a class="button" href="{}">Notify</a>', url)

    notify_link.short_description = 'Notify User'
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('notify-missing/<int:account_id>/', self.admin_site.admin_view(self.notify_missing_view), name='notify_missing_profile'),
        ]
        return custom_urls + urls

    def notify_missing_view(self, request, account_id):
        account = Account.objects.get(pk=account_id)
        
        try:
            profile = Profile.objects.get(account_id=account)
        except Profile.DoesNotExist:
            # Send email immediately using separate function and template
            send_profile_missing_email(account)
            messages.success(request, f"Email sent to {account.email} to complete their profile.")
            return redirect('..')


        if request.method == 'POST':
            missing_items = request.POST.getlist('missing_items')
            edit_link = generate_secure_edit_link(profile, missing_items)

            # Pass the link to the email sender
            send_profile_incomplete_email(account, missing_items, edit_link)
            messages.success(request, f"Email sent to {account.email} regarding missing items.")
            return redirect('..')

        return TemplateResponse(request, 'admin/notify_missing_profile.html', {
            'account': account,
            'missing_fields': ['resume', 'projects/Portfolio'],
        })

# Register the new Account admin


class ProjectAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True

    def owner_name(self, obj):
        return obj.profile.first_name + ' ' + obj.profile.last_name if obj.profile else None
    owner_name.short_description = 'Owner'

    list_display = ['title', 'description', 'pdf_file', 'created_at', 'owner_name', ]
        
class CountryWorkedFilter(admin.SimpleListFilter):
    title = _('Country Worked')
    parameter_name = 'country_worked'

    def lookups(self, request, model_admin):
        past_experiences = PastExperience.objects.values_list('country__country', flat=True).distinct()
        return [(country, country) for country in past_experiences]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(bg_id__past_experiences__country__country=self.value())
        return queryset




from django.contrib.admin import SimpleListFilter
from datetime import date

class AgeRangeFilter(SimpleListFilter):
    title = 'Age Range'
    parameter_name = 'age_range'

    def lookups(self, request, model_admin):
        return [
            ('below_20', '20 and below'),
            ('20_29', '20–29'),
            ('30_39', '30–39'),
            ('40_49', '40–49'),
            ('50_above', '50 and above'),
        ]

    def queryset(self, request, queryset):
        today = date.today()

        def age_to_date(age):
            return date(today.year - age, today.month, today.day)

        if self.value() == 'below_20':
            return queryset.filter(date_of_birth__gt=age_to_date(20))
        elif self.value() == '20_29':
            return queryset.filter(date_of_birth__lte=age_to_date(20), date_of_birth__gt=age_to_date(30))
        elif self.value() == '30_39':
            return queryset.filter(date_of_birth__lte=age_to_date(30), date_of_birth__gt=age_to_date(40))
        elif self.value() == '40_49':
            return queryset.filter(date_of_birth__lte=age_to_date(40), date_of_birth__gt=age_to_date(50))
        elif self.value() == '50_above':
            return queryset.filter(date_of_birth__lte=age_to_date(50))
        return queryset
    
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'view_profile_button', 'df_id', 'first_name', 'last_name', 'suffix', 'middle_name', 
        'barangay', 'date_of_birth', 'contact_no', 'gender',
        'get_affiliation', 'get_specialization', 'get_languages', 'get_skills', 'is_archived',
    ]

    actions = ['export_as_csv', 'export_as_pdf', 'archive_profiles']

    list_filter = [
        'gender',
        AgeRangeFilter,
        'bg_id__affiliation',
        'bg_id__specialization',
        'bg_id__skills',
        'bg_id__language',
        'barangay',
    ]

    search_fields = [
        'df_id',
        'first_name',
        'last_name',
        'middle_name',
        'contact_no',
        'bg_id__skills__skill',          # Search by Skill name
        'bg_id__language__language',        # Search by Language name
        'bg_id__specialization__specialization',  # Search by Specialization name
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    change_list_template = "admin/profile_change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['profile_chart_url'] = '/admin/profile-charts/'
        return super(ProfileAdmin, self).changelist_view(request, extra_context=extra_context)

    def get_affiliation(self, obj):
        return obj.bg_id.affiliation.aff_name if obj.bg_id else None
    get_affiliation.short_description = 'Affiliation'

    def get_specialization(self, obj):
        return obj.bg_id.specialization.specialization if obj.bg_id else None
    get_specialization.short_description = 'Specialization'

    def get_languages(self, obj):
        return ", ".join([language.language for language in obj.bg_id.language.all()]) if obj.bg_id else None
    get_languages.short_description = 'Languages'

    def get_skills(self, obj):
        return ", ".join([skill.skill for skill in obj.bg_id.skills.all()]) if obj.bg_id else None
    get_skills.short_description = 'Skills'

    def get_past_experiences(self, obj):
        return ", ".join([f"{exp.client} ({exp.year}, {exp.country})" for exp in obj.bg_id.past_experiences.all()]) if obj.bg_id else None
    get_past_experiences.short_description = 'Past Experiences'

    def get_resume(self, obj):
        resume = Resume.objects.filter(profile=obj).first()
        return resume.resume_file.url if resume else None
    get_resume.short_description = 'Resume'

    def view_profile_button(self, obj):
        return format_html(
            '<a class="btn btn-primary" href="{}">View</a>',
            reverse('admin_profile_detail', args=[obj.pk])
        )
    view_profile_button.short_description = 'Profile Details'

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="profiles.csv"'
        writer = csv.writer(response)
        # Write headers
        writer.writerow(['ID', 'First Name', 'Last Name', 'Suffix', 'Middle Name', 'Region', 'Province', 'City', 'Barangay', 'ZIP', 'House No', 'Street', 'Date of Birth', 'Contact No', 'Gender', 'Affiliation', 'Specialization', 'Languages', 'Skills', 'Past Experiences', 'Resume'])
        # Write data
        for obj in queryset:
            writer.writerow([
                obj.df_id,
                obj.first_name,
                obj.last_name,
                obj.suffix,
                obj.middle_name,
                obj.region,
                obj.province,
                obj.city,
                obj.barangay,
                obj.zip,
                obj.house_no,
                obj.street,
                obj.date_of_birth,
                obj.contact_no,
                obj.gender,
                self.get_affiliation(obj),
                self.get_specialization(obj),
                self.get_languages(obj),
                self.get_skills(obj),
                self.get_past_experiences(obj),
                self.get_resume(obj),
            ])
        return response

    export_as_csv.short_description = "Export selected profiles as CSV"
    @admin.action(description='Archive selected profiles')
    def archive_profiles(self, request, queryset):
        updated_profiles = queryset.update(is_archived=True)

        # Disable associated accounts
        for profile in queryset:
            account = profile.account_id
            account.is_active = False
            account.save()

        self.message_user(request, f"{updated_profiles} profile(s) successfully archived and associated accounts deactivated.")


class PastExperienceAdmin(admin.ModelAdmin):
    list_display = ['past_exp_id', 'client', 'get_country', 'year']
    list_filter = ['country', 'year']
    def get_country(self, obj):
        return obj.country.country if obj.country else None
    get_country.short_description = 'Country'

    change_list_template = "admin/past_experience_change_list.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['past_experience_chart_url'] = '/admin/past-experience-chart/'
        return super(PastExperienceAdmin, self).changelist_view(request, extra_context=extra_context)
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
    # Add delete_all_none action
    def delete_all_none(self, request, queryset):
        """Delete all PastExperience entries with None values for client, country, and year."""
        deleted_count = PastExperience.objects.filter(client__isnull=True, country__isnull=True, year__isnull=True).delete()[0]
        self.message_user(request, f"Deleted {deleted_count} entries where all fields were None.", level=messages.SUCCESS)

    delete_all_none.short_description = "Delete all past experiences with empty fields"

    actions = [past_exp_export_as_csv, delete_all_none]



admin.site.register(Profile, ProfileAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Account, AccountAdmin)



