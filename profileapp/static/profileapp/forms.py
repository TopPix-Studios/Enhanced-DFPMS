class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['region', 'province', 'city', 'barangay', 'other_fields_here']
