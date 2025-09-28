from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

class UserLoginForm(forms.Form):
    cedula = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not cedula.isdigit():
            raise ValidationError("La cédula debe contener solo números.")
        if not User.objects.filter(username=cedula).exists():
            raise ValidationError("El usuario con esa cédula no existe.")
        return cedula

    def clean(self):
        cleaned_data = super().clean()
        cedula = cleaned_data.get('cedula')
        password = cleaned_data.get('password')

        if cedula and password:
            user = authenticate(username=cedula, password=password)
            if user is None:
                raise ValidationError("Contraseña incorrecta.")
            self.user = user  # guardamos el usuario para usarlo después
        return cleaned_data


class UserRegisterForm(forms.Form):
    cedula = forms.CharField(max_length=20)
    nombre_completo = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not cedula.isdigit():
            raise ValidationError("La cédula debe contener solo números.")
        if User.objects.filter(username=cedula).exists():
            raise ValidationError("Este número de cédula ya está registrado.")
        return cedula

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Correo electrónico no válido.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean_nombre_completo(self):
        nombre = self.cleaned_data.get('nombre_completo')
        if any(char.isdigit() for char in nombre):
            raise ValidationError("El nombre no puede contener números.")
        return nombre
