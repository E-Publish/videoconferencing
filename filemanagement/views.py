import os
import shutil
import zipfile
import xml.etree.ElementTree as Et

from datetime import timedelta, date
from enum import Enum
from pathlib import Path
from threading import Thread

from django.http import FileResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from archivemanager.settings import BBB_VIDEO, DESTINATION, ZIP_PASSWORD

from simpleuserpage.models import ArchivesData


class ArchiveStatus(Enum):
    not_unpacked = 0
    unpacked = 1
    unpacking_process = 2


def find_new_files():
    directory = BBB_VIDEO
    destination = DESTINATION
    lifetime = date.today() + timedelta(days=180)
    event_date = date.today()
    if len(os.listdir(directory)) > 0:
        files = os.listdir(directory)
        for x in range(len(os.listdir(directory))):
            filename = files[x]
            new_archive = ArchivesData(code_name=filename, event_date=event_date, lifetime=lifetime, is_private=True,
                                       is_unremovable=True)
            new_archive.save()
            new_path_dir = os.path.join(destination, os.path.splitext(filename)[0])
            if not os.path.exists(new_path_dir):
                os.mkdir(new_path_dir)
            os.rename(os.path.join(directory, filename), os.path.join(destination, os.path.splitext(filename)[0],
                                                                      filename))


# тестовая функция
def autocomplete_info(filename, new_archive):
    """autocomplete_info(filename: str, new_archive)
    Выполняет парсинг файла событий для автозаполнения информации об архиве,
    работает внутри функции find_new_files()"""

    directory = BBB_VIDEO
    file = f'{filename}.xml'
    file_path = os.path.join(directory, file)
    if os.path.isfile(file_path):

        tree = Et.parse(file_path)
        root = tree.getroot()
        conference_name = ''
        participants_names = []
        all_ids = []
        meeting = root.find('meeting')
        external_id = meeting.get('externalId')

        for event in root.findall('event'):
            if event.get('eventname') == 'ParticipantJoinEvent':
                if event.find('role').text == 'MODERATOR':
                    name = event.find('name').text
                    participants_names.append(name)

        for event in root.findall('event'):
            if event.get('eventname') == 'ParticipantStatusChangeEvent':
                if event.find('status').text == 'role':
                    _id = event.find('userId').text
                    all_ids.append(_id)

        all_ids.sort()
        filtered_ids = list(set(all_ids))

        for _id in filtered_ids:
            for event in root.findall('event'):
                if event.get('eventname') == 'ParticipantJoinEvent':
                    if event.find('userId').text == _id:
                        name = event.find('name').text
                        participants_names.append(name)

        participants_names.sort()
        filtered_participants_names = list(set(participants_names))
        participants_names_string = ','.join(filtered_participants_names)

        for meeting in root.findall('meeting'):
            conference_name = meeting.get('name')
        if "MIR_REG" in external_id:
            new_archive.is_MIR = True
        new_archive.name = conference_name
        new_archive.participants = participants_names_string
        new_archive.description = '-'
        new_archive.save()


def delete_by_lifetime():
    today = timezone.now().date()
    expired_object = ArchivesData.objects.filter(lifetime=today, is_unremovable=False)
    for obj in expired_object:
        directory = DESTINATION
        directory = os.path.join(directory, os.path.splitext(obj.code_name)[0])
        if os.path.exists(directory):
            shutil.rmtree(directory)
        expired_object.delete()


def upload_file(request, id):
    obj = ArchivesData.objects.get(id=id)
    directory = DESTINATION
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


def unpack_zip(request, id):
    archive_info = get_object_or_404(ArchivesData, id=id)
    archive_info.unpacked = ArchiveStatus.unpacking_process.value
    archive_info.save()
    Thread(target=unpack_zip_thread, args=(request, id)).start()
    return redirect('simpleuser_page')


def unpack_zip_thread(request, id):
    password = ZIP_PASSWORD
    archive_info = get_object_or_404(ArchivesData, id=id)
    directory = DESTINATION
    directory = os.path.join(directory, os.path.splitext(archive_info.code_name)[0])
    file_path = os.path.join(directory, archive_info.code_name)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.setpassword(bytes(password, 'utf-8'))
        folder_path = os.path.splitext(file_path)[0]
        zip_ref.extractall(folder_path)

    for file in os.listdir(os.path.join(directory, os.path.splitext(archive_info.code_name)[0])):
        if file.endswith('.mp4'):
            archive_info.recording = file
            archive_info.unpacked = ArchiveStatus.unpacked.value
            archive_info.save()
            break

    directory = os.path.join(
        DESTINATION,
        os.path.splitext(archive_info.code_name)[0],
        os.path.splitext(archive_info.code_name)[0]
    )
    file = 'events.xml'
    file_path = os.path.join(directory, file)
    if os.path.isfile(file_path):

        tree = Et.parse(file_path)
        root = tree.getroot()
        conference_name = ''
        participants_names = []
        all_ids = []

        for event in root.findall('event'):
            if event.get('eventname') == 'ParticipantJoinEvent':
                if event.find('role').text == 'MODERATOR':
                    name = event.find('name').text
                    participants_names.append(name)

        for event in root.findall('event'):
            if event.get('eventname') == 'ParticipantStatusChangeEvent':
                if event.find('status').text == 'role':
                    _id = event.find('userId').text
                    all_ids.append(_id)

        all_ids.sort()
        filtered_ids = list(set(all_ids))

        for _id in filtered_ids:
            for event in root.findall('event'):
                if event.get('eventname') == 'ParticipantJoinEvent':
                    if event.find('userId').text == _id:
                        name = event.find('name').text
                        participants_names.append(name)

        participants_names.sort()
        filtered_participants_names = list(set(participants_names))
        participants_names_string = ','.join(filtered_participants_names)

        for meeting in root.findall('meeting'):
            conference_name = meeting.get('name')
        archive_info.name = conference_name
        archive_info.participants = participants_names_string
        archive_info.description = '-'
        archive_info.save()


def download_file(request, id, handout):
    directory = DESTINATION
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


def download_video(request, id):
    directory = DESTINATION
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


def download_protected_archive(request, id):
    directory = DESTINATION
    obj = ArchivesData.objects.get(id=id)
    archive = os.path.join(directory, os.path.splitext(obj.code_name)[0], obj.code_name)
    if os.path.isfile(archive):
        with open(archive, 'rb') as fh:
            response = FileResponse(open(archive, 'rb'))
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(archive)
            return response
    else:
        return redirect('simpleuser_page')


def download_archive(request, id):
    obj = ArchivesData.objects.get(id=id)

    # название архива, который будет передан пользователю
    zip_name = os.path.join(
        DESTINATION,
        os.path.splitext(obj.code_name)[0],
        f'{os.path.splitext(obj.code_name)[0]}-{obj.event_date}.zip'
    )

    # путь до папки, которую поместим в архив
    zip_path = os.path.join(
        DESTINATION,
        os.path.splitext(obj.code_name)[0],
        os.path.splitext(obj.code_name)[0]
    )

    zip_file = zipfile.ZipFile(zip_name, 'w')

    for root, dirs, files in os.walk(str(zip_path)):
        for file in files:
            file_path = os.path.join(root, file)
            zip_file.write(file_path, file, compress_type=zipfile.ZIP_DEFLATED)

    zip_file.close()

    if os.path.isfile(zip_name):
        response = FileResponse(open(zip_name, 'rb'))
        response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(zip_name)
        return response
    else:
        return redirect('simpleuser_page')


def delete_info(request, id):
    if request.user.is_authenticated and request.user.is_staff:
        obj_to_delete = ArchivesData.objects.get(id=id)
        obj_to_delete.delete()

        # удаление самого архива
        directory = DESTINATION
        directory = os.path.join(directory, os.path.splitext(obj_to_delete.code_name)[0])
        if os.path.exists(directory):
            shutil.rmtree(directory)

        return redirect('simpleuser_page')
    else:
        return redirect('simpleuser_page')
