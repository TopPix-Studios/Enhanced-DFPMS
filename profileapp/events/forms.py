from .models import Event, Location, VirtualDetails, Announcement
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django import forms
from django.contrib import admin


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'image', 'address', 'latitude', 'longitude', 'tags']
    
    # Add a widget with an ID for easy JavaScript selection
    address = forms.CharField(widget=forms.TextInput(attrs={'id': 'address-input'}), required=False, help_text="Leave blank if there is no location.")
    latitude = forms.FloatField(widget=forms.HiddenInput(attrs={'id': 'latitude-input'}))
    longitude = forms.FloatField(widget=forms.HiddenInput(attrs={'id': 'longitude-input'}))

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'organizer',  # This should now be included
            'title', 
            'description', 
            'location_type', 
            'location', 
            'latitude', 
            'longitude', 
            'virtual_url', 
            'virtual_platform', 
            'details', 
            'start_datetime', 
            'end_datetime', 
            'is_published', 
            'is_cancelled',
            'is_moved', 
            'remarks', 
            'tags', 
            'image',
        ]

    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        widget=RelatedFieldWidgetWrapper(
            widget=forms.Select(),
            rel=Event._meta.get_field('location').remote_field,
            admin_site=admin.site,
            can_add_related=True,
            can_change_related=True
        ),
        required=False,
    )

    latitude = forms.FloatField(
        widget=forms.HiddenInput(attrs={'id': 'latitude-input'}),
        required=False,
    )
    longitude = forms.FloatField(
        widget=forms.HiddenInput(attrs={'id': 'longitude-input'}),
        required=False,
    )
    virtual_url = forms.URLField(
        widget=forms.TextInput(attrs={'id': 'id_virtual_url'}),
        required=False,
    )
    virtual_platform = forms.CharField(
        widget=forms.TextInput(attrs={'id': 'id_virtual_platform'}),
        required=False,
    )
    details = forms.CharField(
        widget=forms.TextInput(attrs={'id': 'id_virtual_details'}),
        required=False,
    )
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'id': 'id_remarks'}),
        required=False,
    )

    def save(self, commit=True):
        event = super().save(commit=False)
        
        # Handle the virtual_details field
        virtual_platform = self.cleaned_data.get('virtual_platform')
        virtual_url = self.cleaned_data.get('virtual_url')
        details_str = self.cleaned_data.get('details')

        if virtual_platform and virtual_url and details_str:
            virtual_details_instance, created = VirtualDetails.objects.get_or_create(
                platform=virtual_platform,
                url=virtual_url,
                defaults={'details': details_str}
            )
            event.virtual_details = virtual_details_instance

        if commit:
            event.save()
            self.save_m2m()

        return event
    