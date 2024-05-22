# forms.py
from django import forms
from .models import User,Project,ConnectionDetails
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _

class CustomCreationForm(UserCreationForm,forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class':'form-control', 'type':'password', 'align':'center', 'placeholder':'password'}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={'class':'form-control', 'type':'password', 'align':'center', 'placeholder':' confirm password'}),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name","email",'password1','password2')
        widgets = {
             'first_name': forms.TextInput(attrs={'class': "form-control",'placeholder':'First Name '}),
             'last_name': forms.TextInput(attrs={'class': "form-control",'placeholder':'Last Name '}),
             'email': forms.TextInput(attrs={'class': "form-control",'placeholder':'Email '}),
            
            # 'password1': forms.PasswordInput(attrs={'class': "form-control",'type':'password','placeholder':'Password'}),
            # 'password2': forms.PasswordInput(attrs={'class': "form-control",'placeholder':'Confirm Password'}),
            }
        def clean(self):
            cleaned_data = super(UserForm, self).clean()
            password = cleaned_data.get("password")
            confirm_password = cleaned_data.get("confirm_password")

            if password != confirm_password:
                raise forms.ValidationError(
                    "password and confirm_password does not match"
             )

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'visibility']

class ConnectionDetailsForm(forms.ModelForm):
    class Meta:
        model = ConnectionDetails
        fields = ['connector_type', 'host', 'port', 'username', 'password', 'database_name']
        # widgets = {
        #     'password': forms.PasswordInput(),  # Using PasswordInput widget for the password field
        # }


# class CustomAuthenticationForm(AuthenticationForm):
#     username = forms.EmailField(label=_("Email"), max_length=254)
