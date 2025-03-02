from django.db import models

class Certificate(models.Model):
    student_name = models.CharField(max_length=200)
    course = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    issue_date = models.DateTimeField()
    cert_hash = models.CharField(max_length=66, unique=True)
    ipfs_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate for {self.student_name}"
