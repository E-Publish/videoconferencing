import os
from pathlib import Path
from typing import Generator, IO

from django.contrib.auth.models import User, Group
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.mail import send_mail
from django.core.paginator import *
from django.db.models import Q
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse, HttpResponseNotFound, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string

from archivemanager import settings
from archivemanager.settings import DESTINATION
from filemanagement.views import find_new_files, delete_by_lifetime
from .models import ArchivesData
from .forms import EditArchiveInfoForm, EditUserInfoForm, AddUserForm, TechnicalSupportAddUserForm, \
    TechnicalSupportEditUserInfoForm, LocalAdminAddUserForm, LocalAdminEditUserInfoForm


# вывод информации на страницу и сортировки
def show_archive_data(request):
    mir_page = False
    # нужно для определения группы пользователя
    group_names = request.user.groups.values_list('name', flat=True)

    # фильтрация данных в соответствии с ролями
    if request.user.is_authenticated and request.user.is_staff or "technical_support" in group_names:
        all_data = ArchivesData.objects.filter(is_MIR=False).order_by('id')
        find_new_files()
        delete_by_lifetime()
    elif "technical_support" in group_names:
        all_data = ArchivesData.objects.filter(is_MIR=False).order_by('id')
    elif "local_admin" in group_names:
        all_data = ArchivesData.objects.filter(access=request.user.id).order_by('id')
    elif "common_user" in group_names:
        all_data = ArchivesData.objects.filter(users_list__contains=request.user.id).order_by('id')

    # фильтр "только с записью"
    show_recorded = request.GET.get('show_recorded')
    if show_recorded:
        all_data = ArchivesData.objects.exclude(recording="")

    # фильтр по дате "от - до"
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

    # количество строк на странице по умолчанию
    paginated_data = Paginator(all_data, request.GET.get('lines_per_page', 50))
    page_number = request.GET.get('page')
    page_obj = paginated_data.get_page(page_number)
    return render(request, 'simple_user_page.html', {'page_obj': page_obj,
                                                     'group': group_names,
                                                     'mir_page': mir_page})


# отображение конференций только из мира
def show_mir_archives(request):
    group_names = request.user.groups.values_list('name', flat=True)
    if request.user.is_authenticated and request.user.is_staff or "technical_support" in group_names:
        mir_page = True

        group_names = request.user.groups.values_list('name', flat=True)

        if request.user.is_staff or "technical_support" in group_names:
            find_new_files()
            delete_by_lifetime()

        if request.user.is_staff or "technical_support" in group_names:
            all_data = ArchivesData.objects.filter(is_MIR=True).order_by('id')

            show_recorded = request.GET.get('show_recorded')
            if show_recorded:
                all_data = ArchivesData.objects.exclude(recording="")

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

            paginated_data = Paginator(all_data, request.GET.get('lines_per_page', 50))
            page_number = request.GET.get('page')
            page_obj = paginated_data.get_page(page_number)
            return render(request, 'simple_user_page.html', {'page_obj': page_obj,
                                                             'group': group_names,
                                                             'mir_page': mir_page})
    else:
        return redirect('simpleuser_page', permanent=True)


def link_access_archive(request, id):
    archive_info = get_object_or_404(ArchivesData, id=id)
    archive_info.handout_list = archive_info.handout.split(',')
    archive_info.participants_list = archive_info.participants.split(',')

    if archive_info.access_by_link:
        return render(request, 'free_access_view.html', {'data': archive_info})
    else:
        return HttpResponseNotFound("Запись недоступна, обратитесь к ведущему")


def update_unpacking_progress(request):

    ids = request.GET.getlist('ids[]')
    single_dict = {}
    response_array = []
    for id in ids:
        single_dict = {
            'id': id,
            'progress': ArchivesData.objects.get(id=id).unpacked,
            'recording': ArchivesData.objects.get(id=id).recording,
            'participants': ArchivesData.objects.get(id=id).participants.split(','),
            'name': ArchivesData.objects.get(id=id).name,
            'description': ArchivesData.objects.get(id=id).description
        }
        response_array.append(single_dict)

    return JsonResponse(response_array, safe=False)


def edit_info(request, id):
    group_names = request.user.groups.values_list('name', flat=True)

    if request.user.is_authenticated and request.user.is_staff or "technical_support" or "local_admin" in group_names:
        archive_info = get_object_or_404(ArchivesData, id=id)
        if request.method == "POST":
            form = EditArchiveInfoForm(request.POST, instance=archive_info)
            if form.is_valid():
                archive_info = form.save(commit=False)
                archive_info.save()
                return redirect('simpleuser_page')
        else:
            form = EditArchiveInfoForm(instance=archive_info)
        return render(request, 'edit_info.html', {'form': form, 'group': group_names})
    else:
        return redirect('simpleuser_page', permanent=True)


def admin_panel(request):
    group_names = request.user.groups.values_list('name', flat=True)
    user_group = request.user.groups.values_list('name', flat=True)

    if request.user.is_authenticated and request.user.is_staff:
        users = User.objects.all()

    elif request.user.is_authenticated and "technical_support" in group_names:
        users = User.objects.filter(groups__name='local_admin').order_by('id')

    elif request.user.is_authenticated and "local_admin" in group_names:
        users = User.objects.filter(groups__name='common_user').order_by('id')
    else:
        return redirect('simpleuser_page')

    if request.user.is_authenticated and request.user.is_staff or "technical_support" or "local_admin" in group_names:

        for user in users:
            groups = user.groups.all()
            group_names = [group.name for group in groups]
            user.group_names = group_names

        # здесь указываете количество строк на странице по умолчанию
        paginated_data = Paginator(users, request.GET.get('lines_per_page', 50))
        page_number = request.GET.get('page')
        page_obj = paginated_data.get_page(page_number)

        return render(request, 'admin_panel.html', {'users': page_obj, 'group': user_group})
    else:
        return redirect('simpleuser_page')


def edit_user_info(request, id):
    group_names = request.user.groups.values_list('name', flat=True)

    if request.user.is_authenticated and request.user.is_staff or "local_admin" in group_names:
        user_info = get_object_or_404(User, id=id)
        if request.method == "POST":
            form = EditUserInfoForm(request.POST, instance=user_info)
            if form.is_valid():
                user_info = form.save(commit=False)
                groups = form.cleaned_data['groups']
                if isinstance(groups, Group):
                    groups = [groups]
                user_info.groups.set(groups)
                user_info.save()
                return redirect('admin_panel')
        else:
            if request.user.is_staff:
                form = EditUserInfoForm(instance=user_info)
            elif "technical_support" in group_names:
                form = TechnicalSupportEditUserInfoForm(instance=user_info)
            elif "local_admin" in group_names:
                form = LocalAdminEditUserInfoForm(instance=user_info)
        return render(request, 'edit_user_info.html', {'form': form, 'group': group_names})
    else:
        return redirect('admin_panel', permanent=True)


def delete_user(request, id):
    group_names = request.user.groups.values_list('name', flat=True)
    if request.user.is_authenticated and request.user.is_staff or "technical_support" or "local_admin" in group_names:
        obj_to_delete = User.objects.get(id=id)
        if request.user.id != obj_to_delete:
            obj_to_delete.delete()
            return redirect('admin_panel')
        else:
            return redirect('admin_panel')
    else:
        return redirect('admin_panel')


def add_user(request):
    group_names = request.user.groups.values_list('name', flat=True)
    if request.user.is_authenticated and request.user.is_staff or "technical_support" or "local_admin" in group_names:
        if request.method == 'POST':
            form = AddUserForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = get_random_string(length=10, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)')
                print(f"Пароль: {password}")
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                email = form.cleaned_data.get('email')
                is_staff = form.cleaned_data.get('is_staff')

                User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name,
                                         email=email, is_staff=is_staff)

                user = User.objects.get(email=email)
                groups = form.cleaned_data['groups']
                if isinstance(groups, Group):
                    groups = [groups]
                user.groups.set(groups)

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
            if "technical_support" in group_names:
                form = TechnicalSupportAddUserForm()
            else:
                form = AddUserForm()
            if request.user.is_staff:
                form = AddUserForm()
            elif "technical_support" in group_names:
                form = TechnicalSupportAddUserForm()
            elif "local_admin" in group_names:
                form = LocalAdminAddUserForm()
        return render(request, 'add_user.html', {'form': form, 'group': group_names})
    else:
        return redirect('simpleuser_page')


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


def download_pdf(request, instruction):
    print(instruction)
    file_path = f'simpleuserpage/static/simpleuserpage/pdf/{instruction}.pdf'
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True)
    else:
        return HttpResponse("Файл не найден")
