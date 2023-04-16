from django.db import models


class ArchivesData(models.Model):
    id = models.IntegerField
    name = models.CharField(max_length=30)
    code_name = models.CharField(max_length=30)
    is_private = models.BooleanField()
    event_date = models.DateField()
    lifetime = models.DateField()
    is_unremovable = models.BooleanField()
    participants = models.TextField()
    description = models.TextField()
    handout = models.TextField()
    recording = models.TextField()

    class Meta:
        db_table = 'conference'


