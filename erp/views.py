from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegistrationForm
from purchase.models import Notification
from hrm.models import Employee
from django.contrib.auth.decorators import login_required

from purchase.models import Notification

# Home view (redirects to dashboard for logged-in users)
def home(request):
    return redirect('dashboard')

# Login view
def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            request.session['user_id'] = user.id
            request.session['user_name'] = user.get_full_name() or user.username              
            group = user.groups.first()          
            request.session['department'] = group.name.lower() if group else ''
            return redirect('dashboard')  
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

# Logout view
def logout(request):
    auth_logout(request)
    request.session.flush()  # Clear all session data
    return redirect('login')


# Register view (for new user registration)
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create new user
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            user_name = form.cleaned_data['user_name']
            password = form.cleaned_data['password']
            
            # Ensure unique username and email
            if User.objects.filter(username=user_name).exists():
                form.add_error('user_name', 'Username already exists.')
            elif User.objects.filter(email=email).exists():
                form.add_error('email', 'Email already exists.')
            else:
                # Create the user
                user = User.objects.create_user(username=user_name, email=email, password=password)
                user.first_name = first_name
                user.last_name = last_name
                user.save()
                
                messages.success(request, 'Registration successful! You can now log in.')
                return redirect('login')
    else:
        form = RegistrationForm()
    
    return render(request, 'register.html', {'form': form})

# Dashboard view (only accessible to logged-in users)
# @login_required
# def dashboard(request):
#     notification = Notification.objects.all()
#     return render(request, 'dashboard.html', {'notifications': notification})


@login_required
def dashboard(request):
    user = request.user
    notifications = Notification.objects.filter(
        recipient=user,
        is_read=False
    ).order_by('-created_at')[:10]
    try:
        employee = Employee.objects.get(email=user.email)
    except Employee.DoesNotExist:
        employee = None

    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')[:10]
    unread_count = notifications.count()
    return render(request, 'dashboard.html', {
        'notifications': notifications,
        'employee': employee,        
        'unread_count': unread_count,
    })


