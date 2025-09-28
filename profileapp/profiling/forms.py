from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crispy_forms.bootstrap import Field
from django.forms import formset_factory
from django.core.validators import RegexValidator, MinLengthValidator
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from .models import (
    Account, Profile, Project, BackgroundInformation, Skills,
    PastExperience, Affiliation, Specialization,
    Language, Resume, Country,  Certificate, BackgroundInformationLanguage,
)
from support.models import SupportTicket, Message
from geolocations.models import Region, Province, City, Barangay, Country
from django.urls import reverse
from django.contrib import admin
import re  # Import the re module
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import password_validation
from django.utils import timezone
from django.forms import modelformset_factory

from datetime import timedelta

class AccountForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'Enter your email'}),
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
                message='R400 - Enter a valid email address.',
            )
        ]
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Enter Password', 'class': 'form-control', 'id': 'password-field'}),
        validators=[
            RegexValidator(
                regex=r'^(?=.*\d)(?=.*[a-zA-Z]).{8,}$',
                message='R300 - Password must contain at least one digit and one letter, and be at least 8 characters long.'
            ),
            MinLengthValidator(limit_value=8, message='R200 - Password must be at least 8 characters long.')
        ]
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Confirm Password', 'class': 'form-control', 'id': 'confirm-password-field'}),
        help_text=''
    )

    class Meta:
        model = Account
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autocomplete': 'off', 'placeholder': 'Enter your username'})

        self.fields['password1'].widget.attrs.update({'autocomplete': 'new-password', 'placeholder': 'Enter Password'})
        
        self.fields['password2'].widget.attrs.update({'autocomplete': 'new-password', 'placeholder': 'Confirm Password'})


        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('username', css_class='form-control sign-up-col-1', wrapper_class='mb-3'),
            Field('email', css_class='form-control sign-up-col-1', wrapper_class='mb-3'),
            Field('password1', css_class='form-control sign-up-col-1', wrapper_class='mb-3'),
            Field('password2', css_class='form-control sign-up-col-1', wrapper_class='mb-3'),
            Submit('submit', 'Register', css_class='button-signup'),
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('R600 - The password you entered did not match')    
        return password2

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        
        if password1.isdigit():
            raise forms.ValidationError('R700 - Password cannot be entirely numeric.')
        return password1

    def save(self, commit=True):
        instance = super(AccountForm, self).save(commit=False)
        if commit:
            instance.email = self.cleaned_data['email']
            instance.password = make_password(self.cleaned_data['password1'])
            instance.save()
        return instance
    
class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'Enter your email'}),
    )

class SetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn’t match.")
        return password2

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': 'Username', 'class': 'form-control'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control', 'id': 'password-field'}),
    )

    class Meta:
        model = Account 
        fields = ['username', 'password']
        


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'first_name', 'last_name', 'suffix', 'middle_name',
            'region', 'province', 'city', 'barangay',
            'zip', 'house_no', 'street',
            'date_of_birth', 'contact_no', 'gender', 'picture', 'qoute', 'pronoun', 'is_pwd', 'is_4ps'  # Added fields
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Date of Birth'}),
            'gender': forms.Select(choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer not to say', 'Prefer not to say')],
                                   attrs={'placeholder': 'Select Gender'}),
            'region': forms.Select(attrs={'placeholder': 'Select Region'},
                                   choices=[('', 'Select Region')]),
            'province': forms.Select(attrs={'placeholder': 'Select Province'}),
            'city': forms.Select(attrs={'placeholder': 'Select City/Municipality'}),
            'barangay': forms.Select(attrs={'placeholder': 'Select Barangay'}),
            'zip': forms.TextInput(attrs={'placeholder': 'ZIP Code'}),
            'house_no': forms.TextInput(attrs={'placeholder': 'Building, House No.'}),
            'street': forms.TextInput(attrs={'placeholder': 'Street'}),
            'contact_no': forms.TextInput(attrs={'placeholder': 'Contact Number'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'suffix': forms.TextInput(attrs={'placeholder': 'Suffix', 'required': False}),
            'middle_name': forms.TextInput(attrs={'placeholder': 'Middle Name', 'required': False}),
            'qoute': forms.HiddenInput(),
            'pronoun': forms.HiddenInput(),
            'is_pwd': forms.CheckboxInput(),  # Checkbox for PWD field
            'is_4ps': forms.CheckboxInput(),  # Checkbox for 4Ps field
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

        # Set default values for 'pronoun' and 'qoute' if not provided in initial data
        self.fields['pronoun'].initial = self.fields['pronoun'].initial or 'he/she'
        self.fields['qoute'].initial = self.fields['qoute'].initial or 'Having people acknowledge your existence is a wonderful thing.'

        # Populate choices for the region field from the Region model
        self.fields['region'].queryset = Region.objects.all()
        self.fields['region'].empty_label = "Select Region"
        # Make province, city, and barangay fields initially empty
        self.fields['province'].queryset = Province.objects.none()
        self.fields['city'].queryset = City.objects.none()
        self.fields['barangay'].queryset = Barangay.objects.none()

        # Add a placeholder option for the province, city, and barangay fields
        self.fields['province'].widget.choices = [('', 'Select Province')]
        self.fields['city'].widget.choices = [('', 'Select City/Municipality')]
        self.fields['barangay'].widget.choices = [('', 'Select Barangay')]

        # Add custom JavaScript attributes for dynamic updates
        self.fields['region'].widget.attrs.update({
            'onchange': 'load_provinces(this.value);',
        })
        self.fields['province'].widget.attrs.update({
            'onchange': 'load_cities(this.value);',
        })
        self.fields['city'].widget.attrs.update({
            'onchange': 'load_barangays(this.value);',
        })

        # Manually set choices based on submitted data
        region_id = self.data.get('region')
        province_id = self.data.get('province')
        city_id = self.data.get('city')
        barangay_id = self.data.get('barangay')

        if region_id:
            self.fields['province'].queryset = Province.objects.filter(region_id=region_id)
        if province_id:
            self.fields['city'].queryset = City.objects.filter(province_id=province_id)
        if city_id:
            self.fields['barangay'].queryset = Barangay.objects.filter(city_id=city_id)

    def clean(self):
        cleaned_data = super().clean()
        required_fields = [
            'first_name', 'last_name', 'region', 'province', 'city', 'barangay',
            'zip', 'house_no', 'street', 'date_of_birth', 'contact_no', 'gender',
        ]

        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, ValidationError(f'P{100 + required_fields.index(field)} - This field is required.'))

        # Custom validation for contact_no
        contact_no = cleaned_data.get('contact_no')
        if contact_no and not re.match(r'^\d{10,15}$', contact_no):
            self.add_error('contact_no', ValidationError('P112 - Enter a valid contact number.'))

        # Custom validation for date_of_birth
        date_of_birth = cleaned_data.get('date_of_birth')
        if date_of_birth and not re.match(r'^\d{4}-\d{2}-\d{2}$', str(date_of_birth)):
            self.add_error('date_of_birth', ValidationError('P113 - Enter a valid date in the format YYYY-MM-DD.'))

        if date_of_birth:
            today = timezone.now().date()
            min_birth_date = today - timedelta(days=18 * 365)  # Approximate 18 years

            if date_of_birth > min_birth_date:
                raise ValidationError('You must be at least 18 years old.')
                # Additional validation logic for is_pwd and is_4ps can be added here if needed

            return cleaned_data



class YearField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 4
        super().__init__(*args, **kwargs)
        self.widget.attrs['pattern'] = r'\d{4}'  # Corrected as raw string
        self.widget.attrs['title'] = 'Enter a valid year (e.g., 2022)'

        
class PastExperienceForm(forms.ModelForm):
    client = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Client e.g. Company A',
        }),
    )
    country = forms.ModelChoiceField(queryset=Country.objects.all(),)
    year = forms.DateField(label='Date', widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = PastExperience
        fields = ['client', 'country', 'year']

    def clean(self):
        cleaned_data = super().clean()

        # Safely access the form fields using .get() to avoid KeyError
        client = cleaned_data.get("client")
        country = cleaned_data.get("country")
        year = cleaned_data.get("year")

        # Check if any of the required fields are blank
        if not client:
            raise ValidationError("Client is required.")
        if not country:
            raise ValidationError("Country is required.")
        if not year:
            raise ValidationError("Year is required.")

        return cleaned_data

PastExperienceFormSet = formset_factory(PastExperienceForm, extra=1)


class BackgroundInformationForm(forms.ModelForm):
    languages = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False
    )
    skills = forms.ModelMultipleChoiceField(
        queryset=Skills.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2 skills'}),
        required=False
    )

   

    class Meta:
        model = BackgroundInformation
        fields = ['affiliation', 'specialization', 'languages', 'skills']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['affiliation'].queryset = Affiliation.objects.filter(is_verified=True)
        self.fields['specialization'].queryset = Specialization.objects.all()

        # Add tooltips to language options
        # for language in self.fields['languages'].queryset:
        #     self.fields['languages'].widget.attrs.update({
        #         f'data-toggle-language-{language.id}': language.description
        #     })
    
        # Add tooltips to skill options
        for skill in self.fields['skills'].queryset:
            self.fields['skills'].widget.attrs.update({
                f'data-toggle-skills-{skill.skill_id}': skill.description
            })

    def clean(self):
        cleaned_data = super().clean()
        languages = cleaned_data.get('languages')
        skills = cleaned_data.get('skills')

        if not languages:
            self.add_error('languages', 'Please select at least one language.')
        if not skills:
            self.add_error('skills', 'Please select at least one skill.')

        return cleaned_data


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'pdf_file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get('pdf_file')

        # Check if the PDF file is provided
        if not pdf_file:
            raise forms.ValidationError('A PDF file is required.')

        # Check if the uploaded file is actually a PDF
        if not pdf_file.name.endswith('.pdf'):
            raise forms.ValidationError('The file must be a PDF.')


        return pdf_file
    
ProjectFormSet = modelformset_factory(Project, form=ProjectForm, extra=1, can_delete=True)

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['resume_file']


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['profile', 'certificate_title', 'description', 'issued_by', 'date_issued', 'image_file', 'category']  # Add 'category'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 40, 'placeholder': 'Enter a brief description'}),
            'date_issued': forms.DateInput(attrs={'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'category': forms.Select(attrs={'placeholder': 'Select a category'})  # Add category widget
        }

    def __init__(self, *args, **kwargs):
        super(CertificateForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False

        # Adding placeholders for other fields
        self.fields['profile'].widget.attrs.update({'placeholder': 'Enter your profile information'})
        self.fields['certificate_title'].widget.attrs.update({'placeholder': 'Enter the title of the certificate'})
        self.fields['issued_by'].widget.attrs.update({'placeholder': 'Who issued the certificate?'})
        self.fields['image_file'].widget.attrs.update({'placeholder': 'Upload your certificate image'})
        self.fields['category'].widget.attrs.update({'placeholder': 'Select a category'})


class LanguageForm(forms.ModelForm):
    language = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2', 'style': 'width: 230px'}),
        required=False
    )
     
    class Meta:
        model = BackgroundInformation
        fields = ['language']
        
    def clean(self):
        cleaned_data = super().clean()
        language = cleaned_data.get('language')
        

        if not language:
            self.add_error('language', 'Please select at least one language.')
        
        return cleaned_data

class UpdateLanguageForm(forms.ModelForm):
    language = forms.ModelChoiceField(
        queryset=Language.objects.all(),
        widget=forms.Select(attrs={'class': 'dropdown', 'style': 'width: 230px'}),
        required=True
    )
    proficiency_level = forms.ChoiceField(
        choices=BackgroundInformationLanguage.PROFICIENCY_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'dropdown', 'style': 'width: 230px'}),
        required=True
    )

    class Meta:
        model = BackgroundInformationLanguage
        fields = ['language', 'proficiency_level']

    def clean(self):
        cleaned_data = super().clean()
        language = cleaned_data.get('language')
        proficiency_level = cleaned_data.get('proficiency_level')

        if not language:
            self.add_error('language', 'Please select a language.')
        if not proficiency_level:
            self.add_error('proficiency_level', 'Please select a proficiency level.')

        return cleaned_data

class SkillsForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skills.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        # Add tooltips to language options
        # for language in self.fields['languages'].queryset:
        #     self.fields['languages'].widget.attrs.update({
        #         f'data-toggle-language-{language.id}': language.description
        #     })

        # Add tooltips to skill options
        for skill in self.fields['skills'].queryset:
            self.fields['skills'].widget.attrs.update({
                f'data-toggle-skills-{skill.skill_id}': skill.description
            })

    class Meta:
        model = BackgroundInformation
        fields = ['skills']

    def clean(self):
        cleaned_data = super().clean()
        skills = cleaned_data.get('skills')

        if not skills:
            self.add_error('skills', 'Please select at least one skill.')

        return cleaned_data

class UpdateBackgroundInformationForm(forms.ModelForm):
    class Meta:
        model = BackgroundInformation
        fields = ['affiliation', 'specialization']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set up choices for foreign key fields
        self.fields['affiliation'].queryset = Affiliation.objects.all()
        self.fields['specialization'].queryset = Specialization.objects.all()

        # Set placeholders for fields
        self.fields['affiliation'].widget.attrs['placeholder'] = 'Enter your affiliation'
        self.fields['specialization'].widget.attrs['placeholder'] = 'Enter your specialization'

class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'first_name', 'last_name', 'suffix', 'middle_name',
            'region', 'province', 'city', 'barangay',
            'zip', 'house_no', 'street',
            'date_of_birth', 'contact_no', 'gender', 'picture', 'qoute', 'pronoun'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Date of Birth'}),
            'gender': forms.Select(choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer not to say', 'Prefer not to say')],
                                   attrs={'placeholder': 'Select Gender'}),
            'region': forms.Select(attrs={'placeholder': 'Select Region'}, choices=[('', 'Select Region')]),
            'province': forms.Select(attrs={'placeholder': 'Select Province'}),
            'city': forms.Select(attrs={'placeholder': 'Select City/Municipality'}),
            'barangay': forms.Select(attrs={'placeholder': 'Select Barangay'}),
            'zip': forms.TextInput(attrs={'placeholder': 'ZIP Code'}),
            'house_no': forms.TextInput(attrs={'placeholder': 'House No.'}),
            'street': forms.TextInput(attrs={'placeholder': 'Street'}),
            'contact_no': forms.TextInput(attrs={'placeholder': 'Contact Number'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'suffix': forms.TextInput(attrs={'placeholder': 'Suffix', 'required': False}),
            'middle_name': forms.TextInput(attrs={'placeholder': 'Middle Name', 'required': False}),
            'pronoun': forms.TextInput(attrs={'placeholder': 'Pronoun', 'required': False}),
            'qoute': forms.Textarea(attrs={'placeholder': 'Quote', 'required': False}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Iterate over fields and ensure no required data is lost
        for field in self.Meta.fields:
            if not cleaned_data.get(field) and self.instance:
                cleaned_data[field] = getattr(self.instance, field)

        return cleaned_data

class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Old Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True}),
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = Account  # Assuming Account is your user model
        fields = ['old_password', 'new_password1', 'new_password2']

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        password_validation.validate_password(password1, self.user)
        return password1

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
    
class GuestAttendanceForm(forms.Form):
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

    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'placeholder': 'Enter your name'}))
    age_range = forms.ChoiceField(choices=AGE_RANGES, widget=forms.Select(attrs={'placeholder': 'Select your age range'}))
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select(attrs={'placeholder': 'Select your gender'}))
    pwd = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'placeholder': 'Are you a person with disability?'}))
    four_ps = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'placeholder': 'Are you a 4Ps beneficiary?'}))
    affiliation = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter your affiliation'}))
    contact = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter your contact number'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))







class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...'}),
        }