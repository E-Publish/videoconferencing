from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from loginwindow.forms import AuthUserForm


# Create your views here.
def login_page(request):
    return render(request, 'registration/login.html')


def redirect_to_filemanager(request):
    if request.user.is_authenticated:
        return redirect('simpleuser_page', permanent=True)
    else:
        return redirect('login_page', permanent=True)
