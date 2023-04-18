import os
from datetime import timedelta, date

from archivemanager.settings import BBB_VIDEO, DESTINATION

from simpleuserpage.models import ArchivesData


def find_new_files():
    directory = BBB_VIDEO
    destination = DESTINATION
    lifetime = date.today() + timedelta(days=180)
    if len(os.listdir(directory)) > 0:
        files = os.listdir(directory)
        for x in range(len(os.listdir(directory))):
            filename = files[x]
            newarchive = ArchivesData(code_name=filename, eventdate='2023-03-20', lifetime=lifetime, is_private=True, is_unremovable=True)
            newarchive.save()
            newpathdir = os.path.join(destination, os.path.splitext(filename)[0])
            if not os.path.exists(newpathdir):
                os.mkdir(newpathdir)
            os.rename(os.path.join(directory, filename), os.path.join(destination, os.path.splitext(filename)[0], filename))

