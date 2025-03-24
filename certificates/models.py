from django.db import models

class Certificate(models.Model):
    student_name = models.CharField(max_length=200)
    course = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    issue_date = models.DateTimeField()
    cert_hash = models.CharField(max_length=66, unique=True)
    ipfs_hash = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student_name} - {self.course} ({self.cert_hash})"
