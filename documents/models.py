from django.db import models
from properties.models import Property
from django.contrib.auth.models import User
from properties.models import LandPurchase
from hrm.models import Employee

class PropertyAssociation(models.Model):
    name = models.CharField(max_length=100)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)  # Links to Property model
    
    def __str__(self):
        return self.name


class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    property_association = models.ForeignKey(LandPurchase, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        permissions = [
            ("can_view_document", "Can view document"),
            ("can_upload_document", "Can upload document"),
            ("can_delete_document", "Can delete document"),
            ("can_edit_document", "Can edit document"),
        ]

    def __str__(self):
        return self.title

class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, related_name="versions", on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/versions/')
    version_number = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        permissions = [
            ("can_view_version", "Can view document version"),
            ("can_delete_version", "Can delete document version"),
            ("can_download_version", "Can download document version"),
        ]
    
    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"

class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subfolders', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class File(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='files/')
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
# class UploadedFile(models.Model):
#     file = models.FileField(upload_to='uploads/')  # Path where files will be saved
#     folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
#     uploaded_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.file.name


class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name





class EmpFolder(models.Model):
    name = models.CharField(max_length=255)
    employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='subfolders',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.name}"


class EmpFile(models.Model):
    name = models.CharField(max_length=255)
    employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.CASCADE)
    file = models.FileField(upload_to='emp_files/')
    folder = models.ForeignKey(EmpFolder, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EmpUploadedFile(models.Model):
    file = models.FileField(upload_to='emp_uploads/')
    employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name


class TrackerFolder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subfolders', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def get_breadcrumb(self):
        """Returns list of ancestor folders for breadcrumb navigation."""
        crumbs = []
        folder = self
        while folder:
            crumbs.insert(0, folder)
            folder = folder.parent
        return crumbs


class TrackerFile(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='files/')
    folder = models.ForeignKey(TrackerFolder, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.name
    


class TrackerUploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
        
        

class TrackerGoogleDriveFile(models.Model):
    name = models.CharField(max_length=255, blank=True)
    folder = models.ForeignKey(TrackerFolder, null=True, blank=True, on_delete=models.CASCADE, related_name='google_files')
    created_at = models.DateTimeField(auto_now_add=True)
    google_drive_id = models.CharField(max_length=255, null=True, blank=True)
    google_drive_link = models.URLField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name or self.google_drive_id or 'Drive File'

    @property
    def is_drive_file(self):
        return bool(self.google_drive_id)

    @property
    def preview_url(self):
        if self.google_drive_id:
            return f"https://drive.google.com/file/d/{self.google_drive_id}/preview"
        return None

    @property
    def drive_embed_url(self):
        if self.google_drive_id:
            return f"https://drive.google.com/file/d/{self.google_drive_id}/preview"
        return None