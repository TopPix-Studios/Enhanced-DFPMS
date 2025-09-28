from django.contrib import admin
from support.models import SupportTicket, Message, Notification
from profiling.models import Account
from django.utils import timezone
from django.http import HttpResponse
import csv
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import render, get_object_or_404
from django.contrib import admin
from django.utils.timezone import now
from .models import Message
from django.urls import reverse
from django.db.models import Count, Q

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
# Register your models here.
class MessageInline(admin.StackedInline):
    model = Message
    extra = 1

        # Automatically select the logged-in user in the sender field
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'sender':
            if not request.resolver_match.kwargs.get('object_id'):  # Check if the object is new (no object_id in URL)
                kwargs['initial'] = request.user  # Set the default value to the logged-in user
                kwargs['queryset'] = Account.objects.filter(username=request.user)  # Limit choices to the logged-in user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


        # Automatically assign the logged-in user as the sender when saving the message
    def save_model(self, request, obj, form, change):
        if not obj.sender:
            obj.sender = request.user.account_id  # Set the logged-in user as the message sender
        super().save_model(request, obj, form, change)


class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'status', 'created_at', 'updated_at', 'unread_messages_count', 'view_messages_link']
    list_filter = ['status', 'created_at', 'updated_at']
    inlines = [MessageInline]

   
    def get_queryset(self, request):
        """
        Annotate the queryset with the count of unread messages and total messages,
        and order by updated_at (descending).
        """
        qs = super().get_queryset(request)
        return qs.annotate(
            unread_count=Count(
                'messages',
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)
            ),
            total_messages=Count('messages')  # Annotate total messages for display purposes
        ).order_by('-updated_at')  # Sort by updated_at (most recently updated first)

    def unread_messages_count(self, obj):
        """
        Display the annotated unread message count.
        """
        return obj.unread_count

    unread_messages_count.short_description = 'Unread Messages'

    def view_messages_link(self, obj):
        """
        Create a link to the detailed conversation page for this ticket.
        """
        url = reverse('admin:conversation_detail', args=[obj.id])
        return format_html('<a href="{}" class="button">View Messages</a>', url)

    view_messages_link.short_description = 'Messages'

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        ticket_updated = False
        for instance in instances:
            if isinstance(instance, Message) and not instance.sender:
                instance.sender = request.user
                ticket_updated = True
            instance.save()
        if ticket_updated:
            form.instance.updated_at = now()
            form.instance.save()
        formset.save_m2m()

admin.site.register(SupportTicket, SupportTicketAdmin)


class MessageAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'conversation/<int:ticket_id>/',
                self.admin_site.admin_view(self.conversation_detail),
                name='conversation_detail'
            ),
        ]
        return custom_urls + urls

    def conversation_detail(self, request, ticket_id):
        """Handle conversation details."""
        ticket = get_object_or_404(SupportTicket, id=ticket_id)
        messages = ticket.messages.all().order_by('created_at')
        context = {
            'title': f'Conversation for Ticket: {ticket.subject}',
            'ticket': ticket,
            'messages': messages,
            'opts': self.model._meta,  # Required for admin template rendering
        }
        return render(request, 'admin/conversation_detail.html', context)

# Register the admin without `list_display`, `list_filter`, or `search_fields`
admin.site.register(Message, MessageAdmin)
    
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'announcement', 'event', 'message', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('message', 'user__username', 'announcement__title', 'event__title')
    ordering = ('-created_at',)
    actions = [export_to_csv]