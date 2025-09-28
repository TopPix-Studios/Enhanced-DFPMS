from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import Account, PastExperience, Log, Profile, BackgroundInformation, Resume, Project
from events.models import Event, Announcement
from support.models import SupportTicket, Notification 

@receiver(post_save, sender=Announcement)
def create_announcement_notification(sender, instance, created, **kwargs):
    if created:
        # Notify only verified accounts
        for user in Account.objects.filter(is_verified=True):
            Notification.objects.create(
                user=user,
                notification_type='announcement',
                announcement=instance,
                message=f'New announcement: {instance.title}'
            )


@receiver(pre_save, sender=Event)
def cache_event_state(sender, instance, **kwargs):
    # Cache the previous state of key fields before saving
    if instance.pk:
        previous_instance = sender.objects.get(pk=instance.pk)
        instance._previous_is_cancelled = previous_instance.is_cancelled
        instance._previous_is_moved = previous_instance.is_moved
        instance._previous_start_datetime = previous_instance.start_datetime
        instance._previous_end_datetime = previous_instance.end_datetime
        instance._previous_location = previous_instance.location
    else:
        # If the instance is new, there is no previous state
        instance._previous_is_cancelled = None
        instance._previous_is_moved = None
        instance._previous_start_datetime = None
        instance._previous_end_datetime = None
        instance._previous_location = None


@receiver(post_save, sender=Event)
def create_event_notification(sender, instance, created, **kwargs):
    if created:
        # Notify users when a new event is created
        for user in Account.objects.filter(is_verified=True):
            Notification.objects.create(
                user=user,
                notification_type='event',
                event=instance,
                message=f'New event: {instance.title}'
            )
    else:
        # Check for cancellation
        if instance.is_cancelled and not instance._previous_is_cancelled:
            for user in Account.objects.filter(is_verified=True):
                Notification.objects.create(
                    user=user,
                    notification_type='event',
                    event=instance,
                    message=f'The event "{instance.title}" has been cancelled.'
                )
        
        # Check if the event has been "moved" due to changes in date or location
        if (
            instance.start_datetime != instance._previous_start_datetime or
            instance.end_datetime != instance._previous_end_datetime or
            instance.location != instance._previous_location
        ):
            instance.is_moved = True  # Update the is_moved status
            instance.save(update_fields=['is_moved'])  # Save the update to the database

            for user in Account.objects.filter(is_verified=True):
                Notification.objects.create(
                    user=user,
                    notification_type='event',
                    event=instance,
                    message=f'The event "{instance.title}" has been moved to a new date or location.'
                )
@receiver(post_save, sender=PastExperience)
def delete_empty_past_experience(sender, instance, **kwargs):
    """
    Signal to delete PastExperience instances where all fields are None.
    """
    if instance.client is None and instance.country is None and instance.year is None:
        instance.delete()



# # Helper function to log actions dynamically for any model
# def log_action(user, instance, action, url=None, view_name=None):
#     content_type = ContentType.objects.get_for_model(instance.__class__)
#     Log.objects.create(
#         user=user,
#         content_type=content_type,
#         object_id=instance.pk,
#         action=action,
#         url=url,
#         view_name=view_name,
#         message=f"{action.capitalize()} action performed on {content_type.model} with ID {instance.pk}"
#     )

# @receiver(post_save)
# def log_model_save(sender, instance, created, **kwargs):
#     if sender != Log:  # Prevent logging of Log model itself to avoid recursion
#         action = 'create' if created else 'update'
#         log_action(None, instance, action)  # Replace None with user if available

# @receiver(post_delete)
# def log_model_delete(sender, instance, **kwargs):
#     if sender != Log:  # Prevent logging of Log model itself to avoid recursion
#         log_action(None, instance, 'delete')


@receiver(pre_save, sender=SupportTicket)
def cache_previous_status(sender, instance, **kwargs):
    """
    Cache the previous status of the support ticket before it is saved.
    """
    if instance.pk:  # Ensure this is not a new object
        previous_instance = sender.objects.get(pk=instance.pk)
        instance._previous_status = previous_instance.status

@receiver(post_save, sender=SupportTicket)
def create_support_ticket_notification(sender, instance, created, **kwargs):
    """
    Create notifications for new support tickets or status changes.
    """
    if created:
        # Notify the user of the new support ticket creation
        Notification.objects.create(
            user=instance.user,
            notification_type='support_ticket',
            support_ticket=instance,
            message=f'Your support ticket "{instance.subject}" has been created.'
        )
    else:
        # Notify the user if the support ticket status has changed
        if hasattr(instance, '_previous_status') and instance.status != instance._previous_status:
            Notification.objects.create(
                user=instance.user,
                notification_type='support_ticket',
                support_ticket=instance,
                message=f'Your support ticket "{instance.subject}" status has changed to {instance.get_status_display()}.'
            )


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

@receiver(pre_save, sender=Profile)
def clean_gender_field(sender, instance, **kwargs):
    if instance.gender:
        cleaned_gender = instance.gender.strip().lower()
        instance.gender = GENDER_MAPPING.get(cleaned_gender, instance.gender.lower())


from django.utils.timezone import now
from datetime import timedelta

@receiver(post_save, sender=Log)
def delete_old_logs(sender, instance, **kwargs):
    """
    Deletes log entries older than 30 days every time a new log entry is added.
    """
    expiration_date = now() - timedelta(days=30)
    Log.objects.filter(timestamp__lt=expiration_date).delete()


@receiver(post_save, sender=Notification)
def delete_old_notifications(sender, instance, **kwargs):
    """
    Deletes notifications older than 30 days every time a new notification is added.
    """
    expiration_date = now() - timedelta(days=30)
    Notification.objects.filter(created_at__lt=expiration_date).delete()



def get_changed_fields(instance, old_instance, exclude_fields=["id", "created_at"]):
    if not old_instance:
        return []
    changed = []
    for field in instance._meta.fields:
        name = field.name
        if name in exclude_fields:
            continue
        old_value = getattr(old_instance, name)
        new_value = getattr(instance, name)
        if old_value != new_value:
            changed.append(field.verbose_name or name)
    return changed


### -------- PROFILE --------
@receiver(pre_save, sender=Profile)
def cache_old_profile(sender, instance, **kwargs):
    try:
        instance._old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._old_instance = None


@receiver(post_save, sender=Profile)
def notify_profile_change(sender, instance, created, **kwargs):
    staff_users = Account.objects.filter(is_staff=True)
    if created:
        for user in staff_users:
            Notification.objects.create(
                user=user,
                notification_type='profile',
                message=f"A new profile was created: {instance}."
            )
    else:
        changed_fields = get_changed_fields(instance, instance._old_instance)
        if changed_fields:
            for user in staff_users:
                Notification.objects.create(
                    user=user,
                    notification_type='profile',
                    message=f"Profile '{instance}' updated: {', '.join(changed_fields)}."
                )


### -------- PROJECT --------
@receiver(pre_save, sender=Project)
def cache_old_project(sender, instance, **kwargs):
    try:
        instance._old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._old_instance = None

@receiver(post_save, sender=Project)
def notify_project_change(sender, instance, created, **kwargs):
    staff_users = Account.objects.filter(is_staff=True)
    if created:
        for user in staff_users:
            Notification.objects.create(
                user=user,
                notification_type='profile',
                message=f"New project added: '{instance.title}' by {instance.profile}."
            )
    else:
        changed_fields = get_changed_fields(instance, instance._old_instance)
        if changed_fields:
            for user in staff_users:
                Notification.objects.create(
                    user=user,
                    notification_type='profile',
                    message=f"Project '{instance.title}' updated: {', '.join(changed_fields)}."
                )



### -------- RESUME --------
@receiver(pre_save, sender=Resume)
def cache_old_resume(sender, instance, **kwargs):
    try:
        instance._old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._old_instance = None

@receiver(post_save, sender=Resume)
def notify_resume_change(sender, instance, created, **kwargs):
    staff_users = Account.objects.filter(is_staff=True)
    if created:
        for user in staff_users:
            Notification.objects.create(
                user=user,
                notification_type='profile',
                message=f"A new resume was uploaded for {instance.profile}."
            )
    else:
        changed_fields = get_changed_fields(instance, instance._old_instance)
        if changed_fields:
            for user in staff_users:
                Notification.objects.create(
                    user=user,
                    notification_type='profile',
                    message=f"Resume for {instance.profile} updated: {', '.join(changed_fields)}."
                )

### -------- BACKGROUND INFORMATION --------
@receiver(pre_save, sender=BackgroundInformation)
def cache_old_bginfo(sender, instance, **kwargs):
    try:
        instance._old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._old_instance = None

@receiver(post_save, sender=BackgroundInformation)
def notify_bginfo_change(sender, instance, created, **kwargs):
    try:
        profile = instance.profile_set.first()
    except:
        profile = None

    if not profile:
        return

    staff_users = Account.objects.filter(is_staff=True)

    if created:
        for user in staff_users:
            Notification.objects.create(
                user=user,
                notification_type='profile',
                message=f"New background information added for {profile}."
            )
    else:
        changed_fields = get_changed_fields(instance, instance._old_instance)
        if changed_fields:
            for user in staff_users:
                Notification.objects.create(
                    user=user,
                    notification_type='profile',
                    message=f"Background info for {profile} updated: {', '.join(changed_fields)}."
                )
