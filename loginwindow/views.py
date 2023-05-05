from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from loginwindow.forms import AuthUserForm


# Create your views here.
def login_page(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def redirect_to_filemanager(request):
    if request.user.is_authenticated:
        return redirect('simpleuser_page', permanent=True)
    else:
        return redirect('login_page', permanent=True)
