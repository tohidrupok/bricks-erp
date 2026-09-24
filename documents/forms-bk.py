from django import forms
from .models import Document, Property
from .models import DocumentVersion
from .models import Folder, File, EmpFolder, EmpFile
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
        
        
class EmpFolderForm(forms.ModelForm):

    class Meta:
        model = EmpFolder
        fields = ['name', 'employee']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Folder Name'
            }),

            'employee': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class EmpFileForm(forms.ModelForm):

    class Meta:
        model = EmpFile
        fields = ['name', 'file']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'File Name'
            }),
        }

