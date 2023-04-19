import os
import shutil
import zipfile
from datetime import timedelta, date
from pathlib import Path

from django.http import FileResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from archivemanager.settings import BBB_VIDEO, DESTINATION, ZIP_PASSWORD

from simpleuserpage.models import ArchivesData


def find_new_files():
    directory = BBB_VIDEO
    destination = DESTINATION
    lifetime = date.today() + timedelta(days=180)
    event_date = date.today()
    if len(os.listdir(directory)) > 0:
        files = os.listdir(directory)
        for x in range(len(os.listdir(directory))):
            filename = files[x]
            newarchive = ArchivesData(code_name=filename, event_date=event_date, lifetime=lifetime, is_private=True, is_unremovable=True)
            newarchive.save()
            newpathdir = os.path.join(destination, os.path.splitext(filename)[0])
            if not os.path.exists(newpathdir):
                os.mkdir(newpathdir)
            os.rename(os.path.join(directory, filename), os.path.join(destination, os.path.splitext(filename)[0], filename))


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
            archive_info.save()
            break
    return redirect('simpleuser_page')


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
        with open(zip_name, 'rb') as fh:
            response = FileResponse(fh.read())
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
