import os
from pathlib import Path
from typing import Generator, IO

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import *
from django.db.models import Q
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string

from archivemanager import settings
from archivemanager.settings import DESTINATION
from filemanagement.views import find_new_files, delete_by_lifetime
from .models import ArchivesData
from .forms import EditArchiveInfoForm, EditUserInfoForm, AddUserForm


def show_archive_data(request):
    if request.user.is_staff:
        find_new_files()
        delete_by_lifetime()
    all_data = ArchivesData.objects.all().order_by('id')

    show_recorded = request.GET.get('show_recorded')
    if show_recorded:
        all_data = ArchivesData.objects.exclude(recording="")
    else:
        pass

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if date_from:
        # Используем `time__gte` для выбора записей после `date_from`
        all_data = all_data.filter(event_date__gte=date_from)

    if date_to:
        # Используем `time__lte` для выбора записей до `date_to`
        all_data = all_data.filter(event_date__lte=date_to)

    for obj in all_data:
        obj.handout_list = obj.handout.split(',')

    for obj in all_data:
        obj.participants_list = obj.participants.split(',')

    # здесь указываете количество строк на странице по умолчанию
    paginated_data = Paginator(all_data, request.GET.get('lines_per_page', 50))
    page_number = request.GET.get('page')
    page_obj = paginated_data.get_page(page_number)
    return render(request, 'simple_user_page.html', {'page_obj': page_obj})


def update_unpacking_progress(request):
    id = request.GET.get('id')
    print(id)
    progress = ArchivesData.objects.get(id=id)
    data = {
        'id': id,
        'unpacked': progress.unpacked,
        'recording': progress.recording
    }

    return JsonResponse(data)


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


def admin_panel(request):
    if request.user.is_authenticated and request.user.is_staff:
        users = User.objects.all()
        # здесь указываете количество строк на странице по умолчанию
        paginated_data = Paginator(users, request.GET.get('lines_per_page', 50))
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
            password = get_random_string(length=10, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            email = form.cleaned_data.get('email')
            is_staff = form.cleaned_data.get('is_staff')

            User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name,
                                     email=email, is_staff=is_staff)
            send_mail(
                'Регистрация в корпоративном файловом менеджере',
                f'Вам был создан аккаунт на Epublish File Manager\nvideoconferencing.epublish.ru\nЛогин: {username}\n'
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
    elif field == 'event_date':
        if direction == 'asc':
            archives = archives.order_by('event_date')
            request.session['direction'] = 'desc'
        else:
            archives = archives.order_by('event_date')
            request.session['direction'] = 'asc'

    # Рендерим HTML с отсортированными данными
    return render(request, 'simple_user_page.html', {'page_obj': archives})


def video_player(request, id):
    _video = get_object_or_404(ArchivesData, id=id)
    return render(request, "video_player.html", {"video": _video})


def video_streaming(request, id):
    file, status_code, content_length, content_range = open_file(request, id)
    response = StreamingHttpResponse(file, status=status_code, content_type='video/mp4')

    response['Accept-Ranges'] = 'bytes'
    response['Content-Length'] = str(content_length)
    response['Cache-Control'] = 'no-cache'
    response['Content-Range'] = content_range
    return response


def ranged(
        file: IO[bytes],
        start: int = 0,
        end: int = None,
        block_size: int = 8192,
) -> Generator[bytes, None, None]:
    consumed = 0

    file.seek(start)
    while True:
        data_length = min(block_size, end - start - consumed) if end else block_size
        if data_length <= 0:
            break
        data = file.read(data_length)
        if not data:
            break
        consumed += data_length
        yield data

    if hasattr(file, 'close'):
        file.close()


def open_file(request, video_pk: int) -> tuple:
    _video = get_object_or_404(ArchivesData, pk=video_pk)

    directory = os.path.join(DESTINATION, os.path.splitext(_video.code_name)[0], os.path.splitext(_video.code_name)[0])
    video = _video.recording
    path = os.path.join(directory, video)

    file = open(path, 'rb')
    file_size = os.path.getsize(path)

    content_length = file_size
    status_code = 200
    content_range = request.headers.get('range')

    if content_range is not None:
        content_ranges = content_range.strip().lower().split('=')[-1]
        range_start, range_end, *_ = map(str.strip, (content_ranges + '-').split('-'))
        range_start = max(0, int(range_start)) if range_start else 0
        range_end = min(file_size - 1, int(range_end)) if range_end else file_size - 1
        content_length = (range_end - range_start) + 1
        file = ranged(file, start=range_start, end=range_end + 1)
        status_code = 206
        content_range = f'bytes {range_start}-{range_end}/{file_size}'

    return file, status_code, content_length, content_range
