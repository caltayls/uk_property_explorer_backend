from django.db import models

class RightmoveLocationCodes(models.Model):
    location = models.CharField(max_length=50)
    subDivType = models.CharField(max_length=30)
    locationIdentifier = models.CharField(max_length=30, null=True)
    resultCount = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.location}: {self.locationIdentifier}" 
    
    class Meta:
        ordering = ['location']
        unique_together = ['location', 'subDivType']


class RightmoveProperties(models.Model):
    pass