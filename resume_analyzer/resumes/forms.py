from django import forms
from .models import Resume


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none'
            }),
        }

    def __init__(self, *args, **kwargs):
        # capture user from view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_file(self):
        file = self.cleaned_data.get('file')

        if not file:
            raise forms.ValidationError('Please upload a file.')

        ext = file.name.split('.')[-1].lower()
        if ext not in ['pdf', 'docx']:
            raise forms.ValidationError('Please upload a PDF or DOCX file.')

        return file

    def save(self, commit=True):
        resume = super().save(commit=False)
        if self.user:
            resume.user_id = self.user  # assuming ForeignKey to User model
        if commit:
            resume.save()
        return resume







