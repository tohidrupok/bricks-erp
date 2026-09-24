from django import forms
from .models import Document, Property
from .models import DocumentVersion
from .models import Folder, File, EmpFolder, EmpFile,TrackerFolder,TrackerFile,TrackerGoogleDriveFile
from properties.models import LandPurchase

# class DocumentForm(forms.ModelForm):
#     class Meta:
#         model = Document
#         fields = ['title', 'file', 'document_type', 'property_association']  # property_association should be Property, not PropertyAssociation

#     # Modify the form to show properties instead of PropertyAssociation
#     property_association = forms.ModelChoiceField(
#         queryset=Property.objects.all(),  # Show all properties (not PropertyAssociation)
#         required=False,  # Optional, depending on your requirements
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )


class DocumentForm(forms.ModelForm):
    property_association = forms.ModelChoiceField(
        queryset=LandPurchase.objects.all(),
        required=True
    )

    class Meta:
        model = Document
        fields = ['title', 'file', 'document_type', 'property_association']



class DocumentVersionForm(forms.ModelForm):
    class Meta:
        model = DocumentVersion  # Make sure DocumentVersion is correctly assigned here
        fields = ['file'] 


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['name', 'file']
        
      
        



from django import forms
from .models import EmpFolder, EmpFile, Employee

class EmpFolderForm(forms.ModelForm):
    class Meta:
        model = EmpFolder
        fields = ['name', 'employee', 'parent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Folder Name'}),
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'parent': forms.HiddenInput(), # Kept hidden to auto-populate via view context
        }

class EmpFileForm(forms.ModelForm):
    class Meta:
        model = EmpFile
        fields = ['name', 'file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'File Name'}),
        }

# Forms used for Admin Move feature
class MoveFolderForm(forms.Form):
    target_folder = forms.ModelChoiceField(
        queryset=EmpFolder.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label="Select Destination Folder (Leave empty for Root)"
    )

class MoveFileForm(forms.Form):
    target_folder = forms.ModelChoiceField(
        queryset=EmpFolder.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Select Destination Folder"
    )
    
    
class TrackerFolderForm(forms.ModelForm):
    class Meta:
        model = TrackerFolder
        fields = ['name']

class TrackerFileUploadForm(forms.ModelForm):
    class Meta:
        model = TrackerFile
        fields = ['name', 'file']
        





from documents.google_drive_service import extract_drive_id_from_link, is_folder_link


class TrackerDriveLinkForm(forms.Form):
    name = forms.CharField(
        required=False,
        label="Name",
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter a name for this file...',
        })
    )
    google_drive_link = forms.URLField(
        required=True,
        label="Google Drive Link",
        widget=forms.URLInput(attrs={
            'placeholder': 'https://drive.google.com/file/d/... or /folders/...',
        }),
        help_text="Paste any Google Drive file or folder sharing link."
    )

    def clean_google_drive_link(self):
        link = self.cleaned_data.get('google_drive_link', '').strip()
        drive_id = extract_drive_id_from_link(link)
        if not drive_id:
            raise forms.ValidationError(
                "Could not extract a Drive ID. Please use a valid Google Drive sharing URL."
            )
        self._extracted_drive_id = drive_id
        self._is_folder = is_folder_link(link)
        return link
        
        



# from documents.google_drive_service import extract_drive_id_from_link, is_folder_link


# class TrackerDriveLinkForm(forms.ModelForm):
#     google_drive_link = forms.URLField(
#         required=True,
#         label="Google Drive Link",
#         widget=forms.URLInput(attrs={
#             'placeholder': 'https://drive.google.com/file/d/... or /folders/...',
#         }),
#         help_text="Paste any Google Drive file or folder sharing link."
#     )

#     class Meta:
#         model = TrackerGoogleDriveFile
#         fields = ['google_drive_link']

#     def clean_google_drive_link(self):
#         link = self.cleaned_data.get('google_drive_link', '').strip()

#         drive_id = extract_drive_id_from_link(link)
#         if not drive_id:
#             raise forms.ValidationError(
#                 "Could not extract a Drive ID from this link. Please use a valid Google Drive sharing URL."
#             )

#         # Store on the form instance so the view can access it
#         self._extracted_drive_id = drive_id
#         self._is_folder = is_folder_link(link)

#         return link