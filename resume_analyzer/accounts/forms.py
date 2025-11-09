from django import forms
from django.contrib.auth import get_user_model, login, authenticate
User = get_user_model()
class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        max_length= 255,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def email_clean(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already exists') 
        return email
        
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if(password1 and password2 and password1 != password2):
            raise forms.ValidationError('Password does not match!')
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data.get('password1'))
        if commit:
            user.save()
        return user
    
class LoginForm(forms.Form):
    email = forms.EmailField(label="Email",
                            widget=forms.EmailInput(attrs={'class':'form-control'})
                            )
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput(attrs={'class': 'form-control'})
                            
                               )
    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        user = authenticate(username=email, password=password)

        if not user:
            raise forms.ValidationError('Invalid Email or Paswword')
        self.user = user
        return self.cleaned_data
    
    def get_user(self):
        return self.user


                


