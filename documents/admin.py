from django.contrib import admin

# Register your models here.
from .models import Document, PropertyAssociation, DocumentVersion,File,EmpFolder,EmpFile,TrackerFolder,TrackerFile,TrackerGoogleDriveFile

admin.site.register(Document)
admin.site.register(PropertyAssociation)
admin.site.register(DocumentVersion)
admin.site.register(File)
admin.site.register(EmpFolder)
admin.site.register(EmpFile)
admin.site.register(TrackerFolder)
admin.site.register(TrackerFile)
admin.site.register(TrackerGoogleDriveFile)
