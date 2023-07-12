from django.db import models


class ArchivesData(models.Model):
    id = models.IntegerField
    name = models.CharField(max_length=255)
    code_name = models.CharField(max_length=255)
    is_private = models.BooleanField()
    event_date = models.DateField()
    lifetime = models.DateField()
    is_unremovable = models.BooleanField()
    participants = models.TextField()
    description = models.TextField()
    handout = models.TextField()
    recording = models.TextField()
    unpacked = models.SmallIntegerField(default=0)
    access = models.SmallIntegerField(default=0)
    users_list = models.TextField(default=0)
    access_by_link = models.BooleanField(default=False)

    class Meta:
        db_table = 'conference'

