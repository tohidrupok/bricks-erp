from django.shortcuts import render, redirect, get_object_or_404
from .models import Document, Property
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .forms import DocumentForm
from .forms import DocumentVersionForm
from django.core.paginator import Paginator
import os
from .models import Folder, File, EmpFolder, EmpFile
from .forms import FolderForm, FileUploadForm, EmpFolderForm, EmpFileForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from properties.models import LandPurchase
from hrm.models import Employee
from inventories.utils import log_deleted_data


BASE_DIR = 'http://127.0.0.1:8000/dashboard/display/'


@login_required
def document_list(request, property_id=None):
    if property_id:
        property_obj = get_object_or_404(Property, id=property_id)
        documents = property_obj.documents.all().order_by('id')
        paginator_owners = Paginator(documents, 10)
        page_number_owners = request.GET.get('page')
        documents_owners = paginator_owners.get_page(page_number_owners)
        return render(request, 'documents/document_list.html', {'documents': documents_owners})
    
    else:
        documents = Document.objects.all().order_by('id')
        documents = documents.select_related('property_association')
        paginator = Paginator(documents, 10)
        page_number = request.GET.get('page')
        documents = paginator.get_page(page_number)

        return render(request, 'documents/document_list.html', {'documents': documents})

# @login_required
# def upload_document(request, property_id=None):
#     if property_id:
#         try:            
#             property = Property.objects.get(id=property_id)
#             property_association = None  
#         except Property.DoesNotExist:
#             property = None
#             property_association = None
#     else:
#         property = None
#         property_association = None

#     if request.method == 'POST':
#         form = DocumentForm(request.POST, request.FILES)
        
#         if form.is_valid():           
#             document = form.save(commit=False)
            
#             # If a property is available, assign it
#             if property:
#                 document.property_association = property  # Assign Property instance (NOT PropertyAssociation)
            
#             document.uploaded_by = request.user  # Associate the current user who uploads
#             document.save()  # Save the document to 
#             messages.success(request, 'Document Uploaded successfully!')
#             return redirect('document_list') 
#         else:
#             print(form.errors)  
#             messages.error(request, 'There was an error Uploaded the Document. Please try again.')
#     else:
#         form = DocumentForm()  

#     return render(request, 'documents/upload_document.html', {
#         'form': form, 
#         'property_association': property_association  
#     })


# @login_required
# def upload_document(request):
#     property_association = LandPurchase.objects.all()
#     print(property_association)
#     if request.method == 'POST':
#         form = DocumentForm(request.POST, request.FILES)
        
#         if form.is_valid():           
#             document = form.save(commit=False)
            
#             if property:
#                 document.property_association = property  
            
#             document.uploaded_by = request.user  
#             document.save()  
#             messages.success(request, 'Document Uploaded successfully!')
#             return redirect('document_list') 
#         else:
#             print(form.errors)  
#             messages.error(request, 'There was an error Uploaded the Document. Please try again.')
#     else:
#         form = DocumentForm()  

#     return render(request, 'documents/upload_document.html', {
#         'form': form, 
#         'property_association': property_association  
#     })

@login_required
def upload_document(request):
    property_association = LandPurchase.objects.all()

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user  
            document.save()
            messages.success(request, 'Document Uploaded successfully!')
            return redirect('document_list')
        else:
            print(form.errors)
            messages.error(request, 'There was an error uploading the document. Please try again.')
    else:
        form = DocumentForm()

    return render(request, 'documents/upload_document.html', {
        'form': form,
        'property_association': property_association
    })

@login_required
def document_versions(request, document_id):
    document = get_object_or_404(Document, id=document_id) 
    versions = document.versions.all()  
    return render(request, 'documents/document_versions.html', {
        'document': document,
        'versions': versions
    })


@login_required
def upload_document_version(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        form = DocumentVersionForm(request.POST, request.FILES)
        if form.is_valid():
            version = form.save(commit=False)
            version.document = document  # Link the version to the document
            version.version_number = document.versions.count() + 1  # Auto-increment version number
            version.save()
            return redirect('document_versions', document_id=document.id)  # Redirect back to the versions page

    else:
        form = DocumentVersionForm()

    return render(request, 'documents/upload_document_version.html', {'form': form, 'document': document})


@login_required
def display(request, folder_id=None):
    if folder_id:
        # If folder_id is provided, get the specific folder
        current_folder = get_object_or_404(Folder, pk=folder_id)
    else:
        # If no folder_id is provided, set root folder (None)
        current_folder = None

    # Get subfolders and files for the current folder
    folders = Folder.objects.filter(parent=current_folder)
    files = File.objects.filter(folder=current_folder)

    # Handle folder creation
    if request.method == 'POST' and 'create_folder' in request.POST:
        folder_form = FolderForm(request.POST)
        if folder_form.is_valid():
            new_folder = folder_form.save(commit=False)
            new_folder.parent = current_folder  # Set parent folder if any
            new_folder.save()

            # Check if the request is AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'folder_name': new_folder.name, 'folder_id': new_folder.id})

            # For non-AJAX (regular request), redirect to the folder
            if current_folder is None:
                return redirect('display')  # Redirect to the root view
            else:
                return redirect('display_folder', folder_id=current_folder.id)  # Redirect to specific folder

    else:
        folder_form = FolderForm()

    # Handle file upload
    if request.method == 'POST' and 'upload_file' in request.POST:
        file_form = FileUploadForm(request.POST, request.FILES)
        if file_form.is_valid():
            new_file = file_form.save(commit=False)
            new_file.folder = current_folder
            new_file.save()
            return redirect('display', folder_id=current_folder.id if current_folder else None)
    else:
        file_form = FileUploadForm()

    context = {
        'current_folder': current_folder,
        'folders': folders,
        'files': files,
        'folder_form': folder_form,
        'file_form': file_form,
    }

    return render(request, 'documents/display_file.html', context)

# This is the view to handle file uploads inside a specific folder:
# @login_required
# def page(request, folder_id):
#     # Get the specific folder
#     current_folder = get_object_or_404(Folder, pk=folder_id)
    
#     # Get files in the specific folder
#     files = File.objects.filter(folder=current_folder)
    
#     # Handle file upload
#     if request.method == 'POST' and 'upload_file' in request.POST:
#         file_form = FileUploadForm(request.POST, request.FILES)
#         if file_form.is_valid():
#             new_file = file_form.save(commit=False)
#             new_file.folder = current_folder
#             new_file.save()
#             return redirect('page', folder_id=folder_id)  
#     else:
#         file_form = FileUploadForm()

#     context = {
#         'current_folder': current_folder,
#         'files': files,
#         'file_form': file_form,
#     }

#     return render(request, 'documents/page.html', context)



@login_required
def page(request, folder_id):
    # Get the specific folder
    current_folder = get_object_or_404(Folder, pk=folder_id)
    
    # Get files in the specific folder, sorted by name
    files = File.objects.filter(folder=current_folder).order_by('name')
    
    # Handle file upload
    if request.method == 'POST' and 'upload_file' in request.POST:
        file_form = FileUploadForm(request.POST, request.FILES)
        if file_form.is_valid():
            new_file = file_form.save(commit=False)
            new_file.folder = current_folder
            new_file.save()
            return redirect('page', folder_id=folder_id)  
    else:
        file_form = FileUploadForm()

    context = {
        'current_folder': current_folder,
        'files': files,
        'file_form': file_form,
    }

    return render(request, 'documents/page.html', context)


@login_required
def edit_file_name(request, file_id):
    file_obj = get_object_or_404(File, pk=file_id)

    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        if new_name:
            file_obj.name = new_name
            file_obj.save()
            return redirect('page', folder_id=file_obj.folder.id)
    
    context = {'file': file_obj}
    return render(request, 'documents/edit_file_name.html', context)

# @login_required
# def edit_file_name(request, file_id):
#     if request.method == 'POST':
#         new_name = request.POST.get('new_name', '').strip()
#         file_obj = get_object_or_404(File, pk=file_id)
#         if new_name:
#             import os
#             ext = os.path.splitext(file_obj.file.name)[1]  # keep original extension
#             file_obj.file.name = f"{new_name}{ext}"
#             file_obj.save()
#             return JsonResponse({'status': 'success', 'new_name': file_obj.file.name})
#         return JsonResponse({'status': 'failed', 'error': 'Empty name'})
#     return JsonResponse({'status': 'failed', 'error': 'Invalid request'})
    
    
    

@csrf_protect  # This will ensure CSRF validation is active
@login_required
def rename_folder(request, folder_id):
    # Get the folder by its ID
    folder = get_object_or_404(Folder, pk=folder_id)

    if request.method == 'POST':
        # Get the new name from the POST data
        new_name = request.POST.get('new_name')
        if new_name:
            folder.name = new_name
            folder.save()
            return JsonResponse({'success': True, 'new_name': new_name})
        else:
            return JsonResponse({'success': False, 'error': 'No new name provided'}, status=400)
    
    # If not a POST request, return a form (could be a modal in your UI)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@csrf_protect
@login_required
def delete_folder(request, folder_id):
    folder = get_object_or_404(Folder, pk=folder_id)

    if request.method == 'POST':
        try:
            log_deleted_data(folder, request.user)
            folder.delete()  
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})



@login_required
def create_folder(request):
    folder_name = request.POST.get('folder_name')
    parent_folder = request.GET.get('parent')  # Parent folder passed in the URL

    if folder_name:
        folder_path = os.path.join(BASE_DIR, parent_folder, folder_name) if parent_folder else os.path.join(BASE_DIR, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return HttpResponse(f"Folder '{folder_name}' created successfully.")
        else:
            return HttpResponse(f"Folder '{folder_name}' already exists.")
    return HttpResponse("Folder name is required.")

@login_required
def delete_file(request, file_id):
    # Get the file object or 404 if not found
    file = get_object_or_404(File, id=file_id)

    if request.method == 'POST':
        log_deleted_data(file, request.user)
        file.delete()

        # Show a success message (optional)
        messages.success(request, "File deleted successfully.")

        # Redirect to a page after deletion (change the redirect URL as needed)
        return redirect('display')

    # If the request is not POST, redirect back or handle accordingly
    return redirect('display')




# @login_required
# def emp_document(request, folder_id=None):

#     current_folder = None

#     if folder_id:
#         current_folder = get_object_or_404(EmpFolder, id=folder_id)

#     employee = Employee.objects.filter(user=request.user).first()

#     # ADMIN
#     if request.user.is_superuser:

#         if current_folder:
#             folders = EmpFolder.objects.filter(parent=current_folder)
#         else:
#             folders = EmpFolder.objects.filter(parent=None)

#     # EMPLOYEE
#     else:

#         if current_folder:
#             folders = EmpFolder.objects.filter(
#                 parent=current_folder,
#                 employee=employee
#             )
#         else:
#             folders = EmpFolder.objects.filter(
#                 parent=None,
#                 employee=employee
#             )

#     # CREATE FOLDER
#     if request.method == 'POST' and 'create_folder' in request.POST:

#         folder_form = EmpFolderForm(request.POST)

#         if folder_form.is_valid():

#             folder = folder_form.save(commit=False)

#             folder.parent = current_folder

#             # Employee login automatic employee select
#             if not request.user.is_superuser:
#                 folder.employee = employee

#             folder.save()

#             return redirect(request.path)

#     else:

#         folder_form = EmpFolderForm()

#         # Employee login hide employee field
#         if not request.user.is_superuser:
#             folder_form.fields['employee'].widget = forms.HiddenInput()
#             folder_form.fields['employee'].required = False

#     context = {
#         'folders': folders,
#         'folder_form': folder_form,
#         'current_folder': current_folder,
#     }

#     return render(request, 'documents/emp_display_file.html', context)
    



from collections import OrderedDict



@login_required
def emp_document(request):

    # =========================
    # GET LOGGED IN EMPLOYEE
    # =========================
    employee = Employee.objects.filter(
        user=request.user
    ).first()

    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect('home')

    # =========================
    # CHECK ADMIN
    # =========================
    is_admin = False

    if employee.employee_name:
        is_admin = employee.employee_name.lower() == "admin"

    # =========================
    # ROLE BASED FOLDERS
    # =========================
    if is_admin:

        # ADMIN SEE ALL EMPLOYEE FOLDERS
        folders = EmpFolder.objects.select_related(
            'employee'
        ).order_by(
            'employee__employee_name',
            '-id'
        )

    else:

        # NORMAL USER SEE ONLY OWN
        folders = EmpFolder.objects.filter(
            employee=employee
        ).select_related(
            'employee'
        ).order_by('-id')

    # =========================
    # CREATE FOLDER
    # =========================
    if request.method == 'POST':

        folder_form = EmpFolderForm(request.POST)

        if folder_form.is_valid():

            folder = folder_form.save(commit=False)

            # ADMIN CAN CREATE FOR ANY EMPLOYEE
            if is_admin:

                emp_id = request.POST.get('employee')

                if emp_id:
                    folder.employee_id = emp_id
                else:
                    folder.employee = employee

            # NORMAL USER CREATE OWN FOLDER
            else:

                folder.employee = employee

            folder.save()

            messages.success(
                request,
                "Folder created successfully."
            )

            return redirect('emp_document')

    else:

        folder_form = EmpFolderForm()

        # NORMAL USER
        if not is_admin:

            folder_form.fields['employee'].queryset = Employee.objects.filter(
                id=employee.id
            )

            folder_form.fields['employee'].initial = employee
            folder_form.fields['employee'].disabled = True

    # =========================
    # GROUP BY EMPLOYEE NAME
    # =========================
    grouped_folders = OrderedDict()

    # ADMIN = SHOW ALL EMPLOYEE FOLDERS
    if is_admin:

        for folder in folders:

            emp_name = (
                folder.employee.employee_name
                if folder.employee
                else "Unknown"
            )

            grouped_folders.setdefault(
                emp_name,
                []
            ).append(folder)

    # NORMAL USER = ONLY OWN FOLDERS
    else:

        grouped_folders[employee.employee_name] = list(
            folders
        )

    # =========================
    # CONTEXT
    # =========================
    context = {
        'grouped_folders': grouped_folders,
        'folder_form': folder_form,
        'employee': employee,
        'is_admin': is_admin,
    }

    return render(
        request,
        'documents/emp_display_file.html',
        context
    )
    
    
# =========================================================
# EMPLOYEE PAGE
# =========================================================

@login_required
def emp_page(request, folder_id):

    folder = get_object_or_404(EmpFolder, id=folder_id)

    employee = Employee.objects.filter(user=request.user).first()

    # =====================================================
    # SECURITY
    # =====================================================
    if not request.user.is_superuser:

        if folder.employee != employee:
            messages.error(request, "Permission denied.")
            return redirect('emp_document')

    # =====================================================
    # FILES
    # =====================================================
    files = EmpFile.objects.filter(folder=folder).order_by('-id')

    # =====================================================
    # UPLOAD FILE
    # =====================================================
    if request.method == 'POST':

        file_form = EmpFileForm(request.POST, request.FILES)

        if file_form.is_valid():

            file_obj = file_form.save(commit=False)

            file_obj.folder = folder

            # Employee assign
            if request.user.is_superuser:
                file_obj.employee = folder.employee
            else:
                file_obj.employee = employee

            # File name auto
            if not file_obj.name:
                file_obj.name = request.FILES['file'].name

            file_obj.save()

            messages.success(request, "File uploaded successfully.")

            return redirect('emp_page', folder_id=folder.id)

    else:
        file_form = EmpFileForm()

    context = {
        'folder': folder,
        'files': files,
        'file_form': file_form,
        'employee': employee,
    }

    return render(request, 'documents/emp_page.html', context)


# =========================================================
# EDIT FILE
# =========================================================

@login_required
def emp_edit_file_name(request, file_id):

    file = get_object_or_404(EmpFile, id=file_id)

    employee = Employee.objects.filter(user=request.user).first()

    # SECURITY
    if not request.user.is_superuser:

        if file.employee != employee:
            messages.error(request, "Permission denied.")
            return redirect('emp_document')

    if request.method == 'POST':

        new_name = request.POST.get('name')

        if new_name:
            file.name = new_name
            file.save()

            messages.success(request, "File updated successfully.")

            return redirect('emp_page', folder_id=file.folder.id)

    return render(request, 'documents/emp_edit_file.html', {
        'file': file
    })


# =========================================================
# DELETE FILE
# =========================================================

@login_required
def emp_delete_file(request, file_id):

    file = get_object_or_404(EmpFile, id=file_id)

    employee = Employee.objects.filter(user=request.user).first()

    # SECURITY
    if not request.user.is_superuser:

        if file.employee != employee:
            messages.error(request, "Permission denied.")
            return redirect('emp_document')

    folder_id = file.folder.id

    # delete physical file
    if file.file:
        file.file.delete(save=False)

    file.delete()

    messages.success(request, "File deleted successfully.")

    return redirect('emp_page', folder_id=folder_id)
    
    
    
@login_required
def emp_rename_folder(request, folder_id):

    if request.method == 'POST':

        folder = get_object_or_404(EmpFolder, id=folder_id)

        new_name = request.POST.get('new_name')

        if new_name:
            folder.name = new_name
            folder.save()

            return JsonResponse({
                'success': True,
                'new_name': new_name
            })

    return JsonResponse({
        'success': False
    })
    
    
    
@login_required
def emp_delete_folder(request, folder_id):

    if request.method == 'POST':

        folder = get_object_or_404(EmpFolder, id=folder_id)

        folder.delete()

        return JsonResponse({
            'success': True
        })

    return JsonResponse({
        'success': False
    })
    
    
# @login_required
# def emp_edit_file_name(request, file_id):

#     file = get_object_or_404(EmpFile, id=file_id)

#     if request.method == 'POST':

#         new_name = request.POST.get('name')

#         if new_name:
#             file.name = new_name
#             file.save()

#             return redirect('emp_page', folder_id=file.folder.id)

#     return render(request, 'documents/emp_edit_file.html', {
#         'file': file
#     })
    
    
# @login_required
# def emp_delete_file(request, file_id):

#     file = get_object_or_404(EmpFile, id=file_id)

#     folder_id = file.folder.id

#     # delete physical file
#     if file.file:
#         file.file.delete()

#     file.delete()

#     return redirect('emp_page', folder_id=folder_id)