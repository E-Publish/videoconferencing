import os
import shutil
import zipfile

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import *
from django.db.models import Q
from django.http import HttpResponse, Http404, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import FormView
from pathlib import Path

from archivemanager import settings
from filemanagement.views import find_new_files
from .models import ArchivesData
from .forms import EditArchiveInfoForm, EditUserInfoForm, AddUserForm


def show_archive_data(request):
    if request.user.is_staff:
        find_new_files()
        delete_by_lifetime()
    all_data = ArchivesData.objects.all()

    show_recorded = request.GET.get('show_recorded')
    if show_recorded:
        all_data = ArchivesData.objects.exclude(recording="")
    else:
        pass

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if date_from:
        all_data = all_data.filter(eventdate__gte=date_from)  # Используем `time__gte` для выбора записей после `date_from`

    if date_to:
        all_data = all_data.filter(eventdate__lte=date_to)  # Используем `time__lte` для выбора записей до `date_to`

    for obj in all_data:
        obj.handout_list = obj.handout.split(',')

    for obj in all_data:
        obj.participants_list = obj.participants.split(',')

    paginated_data = Paginator(all_data, request.GET.get('lines_per_page', 50))  # здесь указываете количество строк на странице по умолчанию
    page_number = request.GET.get('page')
    page_obj = paginated_data.get_page(page_number)
    return render(request, 'simple_user_page.html', {'page_obj': page_obj})


def edit_info(request, id):
    if request.user.is_authenticated and request.user.is_staff:
        archive_info = get_object_or_404(ArchivesData, id=id)
        if request.method == "POST":
            form = EditArchiveInfoForm(request.POST, instance=archive_info)
            if form.is_valid():
                archive_info = form.save(commit=False)
                archive_info.save()
                return redirect('simpleuser_page')
        else:
            form = EditArchiveInfoForm(instance=archive_info)
        return render(request, 'edit_info.html', {'form': form})
    else:
        return redirect('simpleuser_page', permanent=True)


def delete_info(request, id):
    if request.user.is_authenticated and request.user.is_staff:
        obj_to_delete = ArchivesData.objects.get(id=id)
        obj_to_delete.delete()

        # удаление самого архива
        directory = 'C:/Users/kleme/Documents/EpublishPath/restrict'
        directory = os.path.join(directory, os.path.splitext(obj_to_delete.code_name)[0])
        if os.path.exists(directory):
            shutil.rmtree(directory)

        return redirect('simpleuser_page')
    else:
        return redirect('simpleuser_page')


def admin_panel(request):
    if request.user.is_authenticated and request.user.is_staff:
        users = User.objects.all()
        paginated_data = Paginator(users, request.GET.get('lines_per_page', 50))  # здесь указываете количество строк на странице по умолчанию
        page_number = request.GET.get('page')
        page_obj = paginated_data.get_page(page_number)
        return render(request, 'admin_panel.html', {'users': page_obj})
    else:
        return redirect('simpleuser_page')


def edit_user_info(request, id):
    if request.user.is_authenticated and request.user.is_staff:
        user_info = get_object_or_404(User, id=id)
        if request.method == "POST":
            form = EditUserInfoForm(request.POST, instance=user_info)
            if form.is_valid():
                user_info = form.save(commit=False)
                user_info.save()
                return redirect('admin_panel')
        else:
            form = EditUserInfoForm(instance=user_info)
        return render(request, 'edit_user_info.html', {'form': form})
    else:
        return redirect('admin_panel', permanent=True)


def delete_user(request, id):
    if request.user.is_authenticated and request.user.is_staff:
        obj_to_delete = User.objects.get(id=id)
        if request.user.id != obj_to_delete:
            obj_to_delete.delete()
            return redirect('admin_panel')
        else:
            return redirect('admin_panel')
    else:
        return redirect('admin_panel')


def add_user(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            email = form.cleaned_data.get('email')
            is_staff = form.cleaned_data.get('is_staff')

            User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name,
                                     email=email, is_staff=is_staff)
            send_mail(
                'Регистрация в корпоративном файловом менеджере\n',
                f'Вам был создан аккаунт на Epublish File Manager\nhttp://localhost:8000/\nЛогин: {username}\n'
                f'Пароль: {password}\n',
                settings.EMAIL_HOST_USER,
                [f'{email}'],
                fail_silently=False
            )
            return redirect('admin_panel')
    else:
        form = AddUserForm()
    return render(request, 'add_user.html', {'form': form})


def search(request):
    query = request.GET.get('q')
    if query:
        results = ArchivesData.objects.filter(Q(name__icontains=query) | Q(participants__icontains=query))
    else:
        results = ArchivesData.objects.all()
    return render(request, 'simple_user_page.html', {'page_obj': results})


def sort_table(request, field):
    # Получаем queryset всех записей
    archives = ArchivesData.objects.all()

    direction = request.session.get('direction', 'asc')

    # Сортируем queryset по выбранному полю
    if field == 'id':
        if direction == 'asc':
            archives = archives.order_by('id')
            request.session['direction'] = 'desc'
        else:
            archives = archives.order_by('-id')
            request.session['direction'] = 'asc'
    elif field == 'name':
        if direction == 'asc':
            archives = archives.order_by('name')
            request.session['direction'] = 'desc'
        else:
            archives = archives.order_by('-name')
            request.session['direction'] = 'asc'
    elif field == 'eventdate':
        if direction == 'asc':
            archives = archives.order_by('eventdate')
            request.session['direction'] = 'desc'
        else:
            archives = archives.order_by('eventdate')
            request.session['direction'] = 'asc'

    # Рендерим HTML с отсортированными данными
    return render(request, 'simple_user_page.html', {'page_obj': archives})


def download_archive(request, id):
    directory = 'C:/Users/kleme/Documents/EpublishPath/restrict'
    obj = ArchivesData.objects.get(id=id)
    directory = os.path.join(directory, os.path.splitext(obj.code_name)[0])
    code_name = obj.code_name
    file_path = os.path.join(directory, code_name)
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as fh:
            response = FileResponse(fh.read())
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            return response
    else:
        return redirect('simpleuser_page')


def download_video(request, id):
    directory = 'C:/Users/kleme/Documents/EpublishPath/restrict'
    obj = ArchivesData.objects.get(id=id)
    directory = os.path.join(directory, os.path.splitext(obj.code_name)[0], os.path.splitext(obj.code_name)[0])
    video = obj.recording
    file_path = os.path.join(directory, video)
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as fh:
            response = FileResponse(fh.read())
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            return response
    else:
        return redirect('simpleuser_page')


def download_file(request, id, handout):
    directory = 'C:/Users/kleme/Documents/EpublishPath/restrict'
    obj = ArchivesData.objects.get(id=id)
    directory = os.path.join(directory, os.path.splitext(obj.code_name)[0], os.path.splitext(obj.code_name)[0])
    file = handout
    file_path = os.path.join(directory, file)
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as fh:
            response = FileResponse(fh.read())
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            return response
    else:
        return redirect('simpleuser_page')


def unpack_zip(request, id):
    password = '757817'
    archive_info = get_object_or_404(ArchivesData, id=id)
    directory = 'C:/Users/kleme/Documents/EpublishPath/restrict/'
    directory = os.path.join(directory, os.path.splitext(archive_info.code_name)[0])
    file_path = os.path.join(directory, archive_info.code_name)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.setpassword(bytes(password, 'utf-8'))
        folder_path = os.path.splitext(file_path)[0]
        zip_ref.extractall(folder_path)

    for file in os.listdir(os.path.join(directory, os.path.splitext(archive_info.code_name)[0])):
        if file.endswith('.mp4'):
            archive_info.recording = file
            archive_info.save()
            break
    return redirect('simpleuser_page')


def upload_file(request, id):
    obj = ArchivesData.objects.get(id=id)
    directory = 'C:/Users/kleme/Documents/EpublishPath/restrict/'
    directory = os.path.join(directory, os.path.splitext(obj.code_name)[0], os.path.splitext(obj.code_name)[0])
    if request.method == 'POST':
        myfile = request.FILES['myfile']
        directory = Path(directory)/myfile.name
        with directory.open('wb+') as destination:
            for chunk in myfile.chunks():
                destination.write(chunk)

            if obj.handout:
                obj.handout += f",{myfile.name}"
            else:
                obj.handout = myfile.name
            obj.save()
        return redirect('simpleuser_page')
    return render(request, 'upload.html')


def delete_by_lifetime():
    today = timezone.now().date()
    expired_object = ArchivesData.objects.filter(lifetime=today, is_unremovable=False)
    for obj in expired_object:
        directory = 'C:/Users/kleme/Documents/EpublishPath/restrict'
        directory = os.path.join(directory, os.path.splitext(obj.code_name)[0])
        if os.path.exists(directory):
            shutil.rmtree(directory)
        expired_object.delete()
