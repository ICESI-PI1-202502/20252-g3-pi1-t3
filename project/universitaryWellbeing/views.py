from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect, render
from .models import Preferencias, Actividades

# Create your views here.
def user_login(request):
    if request.method == "POST":
        cedula_input = request.POST.get("cedula", "").strip()
        password = request.POST.get("password", "")

        if not User.objects.filter(username=cedula_input).exists():
            messages.error(request, "El usuario con esa cédula no existe")
            return redirect("login")

        user = authenticate(request, username=cedula_input, password=password)

        if user is not None:
            login(request, user)
            if is_role_admin(user):
                return redirect("admin:index")  # admin Django
            return redirect("home")
        else:
            messages.error(request, "Contraseña incorrecta")
            return redirect("user_login")

    # GET → mostrar formulario vacío
    return render(request, "login.html", {})


def register(request):
    if request.method == "POST":
        # Recupera todos los parámetros del POST
        cedula_input = request.POST.get("cedula", "").strip()
        name = request.POST.get("nombre", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        # Verifica si ya existe un usuario con esa cédula
        if get_user_model().objects.filter(cedula=cedula_input).exists():
            messages.error(request, "Ya existe un usuario con esa cédula")
            return redirect("register")
        
          # Validación del correo electrónico usando `validate_email`
        try:
            validate_email(email)  # Intentamos validar el email
        except ValidationError:
            messages.error(request, "El correo electrónico no es válido.")
            return redirect("register")
        
        # Verifica si el correo electrónico ya está registrado
        if get_user_model().objects.filter(email=email).exists():
            messages.error(request, "Este correo electrónico ya está registrado.")
            return redirect("register")
        

        # Crea un nuevo usuario con todos los campos necesarios
        user = get_user_model().objects.create_user(
            username=cedula_input,  # Usamos cédula como username
            password=password,
            email=email,
            cedula=cedula_input,
            nombre=name,
        )
        
        messages.success(request, "Usuario registrado con éxito. Ahora puede iniciar sesión.")
        return redirect("login")

    return render(request, "auth/register.html")



def user_logout(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente")
    return redirect("login")

def is_role_admin(user):
    return user.groups.filter(name="admin").exists() or user.is_superuser


#@login_required
def preferences(request):
    if request.method == 'POST':
        # Obtener las categorías seleccionadas del formulario
        selected_categories = request.POST.getlist('categories')  # Esto obtiene una lista de categorías seleccionadas
        
        # Guardar las categorías seleccionadas en la sesión para usarlas en la siguiente vista
        request.session['selected_categories'] = selected_categories
        
        # Redirigir a la vista de selección de subcategorías
        return redirect('preferences2')

    # Si el método es GET, simplemente mostramos el formulario de categorías
    categories = ['Música','Deportes', 'Proyección Social','Tecnología', 'Artes Escenicas y Danza'
                  , 'Artes Visuales y Plásticas','Programa"Estás en Casa"','Actividad Física y Bienestar', 'Bienestar y Desarrollo Humano']
    return render(request, 'list_preferences_1.html', {'categories': categories})

#@login_required
def preferences2(request):
    if request.method == 'POST':
        # Obtener las subcategorías seleccionadas del formulario
        selected_subcategories = request.POST.getlist('subcategories')  # Lista de subcategorías seleccionadas
        
        # Obtener las categorías seleccionadas de la sesión
        selected_categories = request.session.get('selected_categories', [])
        
        # Guardar las preferencias del usuario
        preference, created = preferences.objects.get_or_create(user=request.user)
        preference.category = ', '.join(selected_categories)  # Guardamos las categorías como una cadena
        preference.subcategory = ', '.join(selected_subcategories)  # Guardamos las subcategorías
        preference.save()

        # Redirigir a la siguiente página, por ejemplo, a recomendaciones
        return redirect('recommendations')  # Cambia a la vista donde mostrarás las recomendaciones

    # Si el método es GET, mostramos el formulario para las subcategorías
    selected_categories = request.session.get('selected_categories', [])
    
    # Aquí debes definir las subcategorías para cada categoría seleccionada
    subcategories = {
        'Deportes': ['Fútbol', 'Basketball', 'Tennis'],
        'Tecnología': ['Computadoras', 'Móviles', 'Electrónica'],
        'Arte': ['Pintura', 'Escultura', 'Fotografía'],
        'Música': ['Rock', 'Pop', 'Jazz'],
    }
    
    # Filtrar las subcategorías basadas en las categorías seleccionadas
    available_subcategories = []
    for category in selected_categories:
        available_subcategories.extend(subcategories.get(category, []))
    
    return render(request, 'list_preferences_2.html', {'subcategories': available_subcategories})



def home_user(request):
    data = Actividades.objects.values("nombre")  # asumiendo que el campo se llama 'nombre'
    return render(request, 'home_user.html', {"actividades": data})

def home_admin(request):
    return render(request, "home_admin.html")






 













