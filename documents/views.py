from django.shortcuts import render, redirect, get_object_or_404
from .models import Document, Property
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .forms import DocumentForm
from .forms import DocumentVersionForm
from django.core.paginator import Paginator
import os
from .models import Folder, File, EmpFolder, EmpFile,TrackerFolder,TrackerFile
from .forms import FolderForm, FileUploadForm, EmpFolderForm, EmpFileForm,TrackerFolderForm,TrackerFileUploadForm,TrackerGoogleDriveFile,TrackerDriveLinkForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from properties.models import LandPurchase
from hrm.models import Employee
from inventories.utils import log_deleted_data
from django.utils import timezone



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





@login_required
def tracker_display(request, folder_id=None):
    if folder_id:
        # If folder_id is provided, get the specific folder
        tracker_create_folder = get_object_or_404(TrackerFolder, pk=folder_id)
    else:
        # If no folder_id is provided, set root folder (None)
        tracker_create_folder = None

    # Get subfolders and files for the current folder
    folders = TrackerFolder.objects.filter(parent=tracker_create_folder)
    files = TrackerFile.objects.filter(folder=tracker_create_folder)

    # Handle folder creation
    if request.method == 'POST' and 'tracker_create_folder' in request.POST:
        folder_form = TrackerFolderForm(request.POST)
        if folder_form.is_valid():
            new_folder = folder_form.save(commit=False)
            new_folder.parent = tracker_create_folder  # Set parent folder if any
            new_folder.save()

            # Check if the request is AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'folder_name': new_folder.name, 'folder_id': new_folder.id})

            # For non-AJAX (regular request), redirect to the folder
            if tracker_create_folder is None:
                return redirect('tracker_display')  # Redirect to the root view
            else:
                return redirect('tracker_display', folder_id=tracker_create_folder.id)  # Redirect to specific folder

    else:
        folder_form = TrackerFolderForm()

    # Handle file upload
    if request.method == 'POST' and 'tracker_upload_file' in request.POST:
        file_form = TrackerFileUploadForm(request.POST, request.FILES)
        if file_form.is_valid():
            new_file = file_form.save(commit=False)
            new_file.folder = tracker_create_folder
            new_file.save()
            return redirect('tracker_display', folder_id=tracker_create_folder.id if tracker_create_folder else None)
    else:
        file_form = TrackerFileUploadForm()

    context = {
        'current_folder': tracker_create_folder,
        'folders': folders,
        'files': files,
        'folder_form': folder_form,
        'file_form': file_form,
    }

    return render(request, 'documents/tracker_display_file.html', context)
    
    


@login_required
def tracker_page(request, folder_id):
    # Get the specific folder
    tracker_create_folder = get_object_or_404(TrackerFolder, pk=folder_id)
    
    # Get files in the specific folder, sorted by name
    files = TrackerFile.objects.filter(folder=tracker_create_folder).order_by('name')
    
    # Handle file upload
    if request.method == 'POST' and 'tracker_upload_file' in request.POST:
        file_form = TrackerFileUploadForm(request.POST, request.FILES)
        if file_form.is_valid():
            new_file = file_form.save(commit=False)
            new_file.folder = tracker_create_folder
            new_file.save()
            return redirect('tracker_page', folder_id=folder_id)  
    else:
        file_form = TrackerFileUploadForm()

    context = {
        'current_folder': tracker_create_folder,
        'files': files,
        'file_form': file_form,
    }

    return render(request, 'documents/tracker_page.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse

from documents.models import TrackerFolder, TrackerGoogleDriveFile
from documents.forms import TrackerDriveLinkForm
from documents.google_drive_service import (
    extract_drive_id_from_link,
    is_folder_link,
    get_drive_file_metadata,
    list_drive_folder_contents,
)


def _do_sync(link, db_folder, custom_name=''):
    """
    Extract Drive ID from link, detect file vs folder,
    save records to DB. Returns (synced_count, is_folder).
    custom_name: if provided, overrides the Drive filename (single file only).
    """
    drive_id = extract_drive_id_from_link(link)
    folder   = is_folder_link(link)
    synced   = 0

    if not drive_id:
        raise ValueError("Could not extract Drive ID from link.")

    if folder:
        # Sync entire folder contents — custom_name ignored for bulk
        contents = list_drive_folder_contents(drive_id)
        for drive_file in contents.get('files', []):
            try:
                file_name = (drive_file.get('name') or 'Untitled').strip()
                file_id   = drive_file.get('id', '')
                file_link = drive_file.get('webViewLink', '')

                if not file_id:
                    continue

                obj, created = TrackerGoogleDriveFile.objects.get_or_create(
                    google_drive_id=file_id,
                    defaults={
                        'name':              file_name,
                        'folder':            db_folder,
                        'google_drive_link': file_link,
                        'last_synced_at':    timezone.now(),
                    }
                )
                if not created:
                    obj.name              = file_name
                    obj.folder            = db_folder
                    obj.google_drive_link = file_link
                    obj.last_synced_at    = timezone.now()
                    obj.save()

                synced += 1

            except Exception as e:
                print(f"[sync] skip file: {e}")
                continue

    else:
        # Sync single file
        meta      = get_drive_file_metadata(drive_id)
        drive_name = (meta.get('name') or 'Drive File').strip() if meta else 'Drive File'
        file_link  = meta.get('webViewLink', link) if meta else link

        # Use custom name if provided, otherwise fall back to Drive name
        file_name = custom_name.strip() if custom_name and custom_name.strip() else drive_name

        obj, created = TrackerGoogleDriveFile.objects.get_or_create(
            google_drive_id=drive_id,
            defaults={
                'name':              file_name,
                'folder':            db_folder,
                'google_drive_link': file_link,
                'last_synced_at':    timezone.now(),
            }
        )
        if not created:
            # Only overwrite name if user explicitly provided one
            if custom_name and custom_name.strip():
                obj.name = file_name
            else:
                obj.name = drive_name
            obj.folder            = db_folder
            obj.google_drive_link = file_link
            obj.last_synced_at    = timezone.now()
            obj.save()

        synced += 1

    return synced, folder


@login_required
def google_tracker_file_system(request, folder_id=None):
    # Resolve current folder
    if folder_id:
        current_folder = get_object_or_404(TrackerFolder, id=folder_id)
    else:
        current_folder = TrackerFolder.objects.filter(parent=None).first()
        if not current_folder:
            current_folder = TrackerFolder.objects.create(name="Root")

    search_query = request.GET.get('q', '')
    files_qs = TrackerGoogleDriveFile.objects.filter(
        folder=current_folder
    ).order_by('-created_at')
    if search_query:
        files_qs = files_qs.filter(name__icontains=search_query)

    if request.method == 'POST' and 'save_drive_link' in request.POST:
        form = TrackerDriveLinkForm(request.POST)
        if form.is_valid():
            link        = form.cleaned_data['google_drive_link']
            custom_name = form.cleaned_data.get('name', '').strip()  # ← get name
            try:
                synced, folder_flag = _do_sync(link, current_folder, custom_name)
                if folder_flag:
                    messages.success(
                        request,
                        f'Google Drive folder synced — {synced} file(s) imported.'
                    )
                else:
                    label = custom_name or 'Google Drive file'
                    messages.success(
                        request,
                        f'"{label}" saved successfully.'
                    )
            except Exception as e:
                err = str(e).encode('utf-8', errors='replace').decode('utf-8')
                messages.error(request, f'Sync failed: {err}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')

        if folder_id:
            return redirect('google_tracker_file_system_folder', folder_id=folder_id)
        return redirect('google_tracker_file_system')

    else:
        form = TrackerDriveLinkForm()

    sub_folders = TrackerFolder.objects.filter(parent=current_folder)
    breadcrumb  = current_folder.get_breadcrumb()

    return render(request, 'documents/google_file_system.html', {
        'current_folder': current_folder,
        'files':          files_qs,
        'form':           form,
        'search_query':   search_query,
        'sub_folders':    sub_folders,
        'breadcrumb':     breadcrumb,
    })


@login_required
def google_tracker_sync_drive(request, folder_id):
    """Re-sync metadata for all Drive-linked files in this folder."""
    folder = get_object_or_404(TrackerFolder, id=folder_id)
    files  = TrackerGoogleDriveFile.objects.filter(
        folder=folder,
        google_drive_id__isnull=False
    ).exclude(google_drive_id='')
    synced = 0

    for f in files:
        try:
            meta = get_drive_file_metadata(f.google_drive_id)
            if meta:
                # Re-sync only updates Drive name if user hasn't set a custom one
                f.name           = (meta.get('name') or f.name).strip()
                f.last_synced_at = timezone.now()
                f.save()
                synced += 1
        except Exception as e:
            print(f"[resync] skip {f.google_drive_id}: {e}")
            continue

    messages.success(request, f'Re-synced {synced} file(s) with Google Drive.')
    return redirect('google_tracker_file_system_folder', folder_id=folder_id)


@login_required
def google_tracker_delete_file(request, file_id):
    file_obj  = get_object_or_404(TrackerGoogleDriveFile, id=file_id)
    folder_id = file_obj.folder_id
    if request.method == 'POST':
        file_obj.delete()
        messages.success(request, 'File record removed.')
    return redirect('google_tracker_file_system_folder', folder_id=folder_id)


@login_required
def google_tracker_edit_file_name(request, file_id):
    file_obj = get_object_or_404(TrackerGoogleDriveFile, id=file_id)
    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        if new_name:
            file_obj.name = new_name
            file_obj.save()
            messages.success(request, 'Name updated.')
        return redirect(
            'google_tracker_file_system_folder',
            folder_id=file_obj.folder_id
        )
    return render(request, 'documents/google_edit_file_name.html', {
        'file_obj': file_obj
    })


@login_required
def google_tracker_drive_browse(request):
    """AJAX: GET ?folder_id=XXX returns Drive folder contents as JSON."""
    folder_id = request.GET.get('folder_id')
    if not folder_id:
        return JsonResponse({'success': False, 'error': 'folder_id required'}, status=400)
    try:
        result = list_drive_folder_contents(folder_id)
        return JsonResponse({'success': True, 'data': result})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def google_drive_test_save(request):
    folder = TrackerFolder.objects.filter(parent=None).first()
    obj    = TrackerGoogleDriveFile.objects.create(
        name              = 'TEST FILE',
        folder            = folder,
        google_drive_id   = 'test_debug_123',
        google_drive_link = 'https://drive.google.com/test',
        last_synced_at    = timezone.now(),
    )
    return JsonResponse({'created_id': obj.id, 'name': obj.name, 'folder': str(folder)})


@login_required
def google_drive_test_api(request):
    """Visit /google-drive/test-api/?folder_id=YOUR_DRIVE_FOLDER_ID"""
    folder_id = request.GET.get('folder_id', '')
    if not folder_id:
        return JsonResponse({'error': 'pass ?folder_id=YOUR_ID'})
    try:
        result = list_drive_folder_contents(folder_id)
        return JsonResponse({
            'files_found':   len(result['files']),
            'folders_found': len(result['folders']),
            'files':         [f['name'] for f in result['files']],
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})
        

# import re
# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth.decorators import login_required
# from .models import TrackerFolder, TrackerFile
# from .forms import TrackerFileUploadForm # Ensure this matches your form import

# @login_required
# def tracker_page(request, folder_id):
#     # Get the specific folder
#     tracker_create_folder = get_object_or_404(TrackerFolder, pk=folder_id)
    
#     # Handle search filtering inside this specific folder page
#     search_query = request.GET.get('search', '').strip()
    
#     # Get files in the specific folder, sorted by name
#     files_queryset = TrackerFile.objects.filter(folder=tracker_create_folder).order_by('name')
    
#     if search_query:
#         files_queryset = files_queryset.filter(name__icontains=search_query)
    
#     # Process files to extract Google Drive IDs dynamically if they are pasted as links
#     processed_files = []
#     for f in files_queryset:
#         drive_id = None
#         # Check if user saved a Google Drive share link in the name field
#         if "drive.google.com" in f.name:
#             # Regex to pull out the unique ID from a Google Drive URL string
#             match = re.search(r'/d/([a-zA-Z0-9-_]+)', f.name)
#             if match:
#                 drive_id = match.group(1)
        
#         processed_files.append({
#             'obj': f,
#             'drive_id': drive_id
#         })
    
#     # Handle file upload (Kept completely original)
#     if request.method == 'POST' and 'tracker_upload_file' in request.POST:
#         file_form = TrackerFileUploadForm(request.POST, request.FILES)
#         if file_form.is_valid():
#             new_file = file_form.save(commit=False)
#             new_file.folder = tracker_create_folder
#             new_file.save()
#             return redirect('tracker_page', folder_id=folder_id)  
#     else:
#         file_form = TrackerFileUploadForm()

#     context = {
#         'current_folder': tracker_create_folder,
#         'files': processed_files, # Use the processed list with parsed IDs
#         'file_form': file_form,
#         'search_query': search_query,
#     }

#     return render(request, 'documents/tracker_page.html', context)
    
@login_required
def tracker_edit_file_name(request, file_id):
    file_obj = get_object_or_404(TrackerFile, pk=file_id)

    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        if new_name:
            file_obj.name = new_name
            file_obj.save()
            return redirect('tracker_page', folder_id=file_obj.folder.id)
    
    context = {'file': file_obj}
    return render(request, 'documents/tracker_edit_file_name.html', context)
    
    
@csrf_protect  # This will ensure CSRF validation is active
@login_required
def tracker_rename_folder(request, folder_id):
    # Get the folder by its ID
    folder = get_object_or_404(TrackerFolder, pk=folder_id)

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
def tracker_delete_folder(request, folder_id):
    folder = get_object_or_404(TrackerFolder, pk=folder_id)

    if request.method == 'POST':
        try:
            log_deleted_data(folder, request.user)
            folder.delete()  
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})



@login_required
def tracker_create_folder(request):
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
def tracker_delete_file(request, file_id):
    # Get the file object or 404 if not found
    file = get_object_or_404(TrackerFile, id=file_id)

    if request.method == 'POST':
        log_deleted_data(file, request.user)
        file.delete()

        # Show a success message (optional)
        messages.success(request, "File deleted successfully.")

        # Redirect to a page after deletion (change the redirect URL as needed)
        return redirect('tracker_display')

    # If the request is not POST, redirect back or handle accordingly
    return redirect('tracker_display')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from collections import OrderedDict
from .models import Employee, EmpFolder, EmpFile
from .forms import EmpFolderForm, EmpFileForm, MoveFolderForm, MoveFileForm

@login_required
def emp_document(request):
    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect('home')

    #is_admin = employee.employee_name.lower() == "admin" if employee.employee_name else False
    is_admin = (
        employee.employee_name.lower() == "admin" or
        employee.employee_name.lower() == "md hanjala"
    ) if employee.employee_name else False

    # ONLY GET ROOT FOLDERS (parent is None)
    if is_admin:
        folders = EmpFolder.objects.filter(parent__isnull=True).select_related('employee').order_by('employee__employee_name', '-id')
    else:
        folders = EmpFolder.objects.filter(employee=employee, parent__isnull=True).select_related('employee').order_by('-id')

    if request.method == 'POST':
        folder_form = EmpFolderForm(request.POST)
        if folder_form.is_valid():
            folder = folder_form.save(commit=False)
            if is_admin:
                emp_id = request.POST.get('employee')
                folder.employee_id = emp_id if emp_id else employee.id
            else:
                folder.employee = employee
            folder.save()
            messages.success(request, "Root folder created successfully.")
            return redirect('emp_document')
    else:
        folder_form = EmpFolderForm()
        if not is_admin:
            folder_form.fields['employee'].queryset = Employee.objects.filter(id=employee.id)
            folder_form.fields['employee'].initial = employee
            folder_form.fields['employee'].disabled = True

    grouped_folders = OrderedDict()
    if is_admin:
        for folder in folders:
            emp_name = folder.employee.employee_name if folder.employee else "Unknown"
            grouped_folders.setdefault(emp_name, []).append(folder)
    else:
        grouped_folders[employee.employee_name] = list(folders)

    context = {
        'grouped_folders': grouped_folders,
        'folder_form': folder_form,
        'employee': employee,
        'is_admin': is_admin,
    }
    return render(request, 'documents/emp_display_file.html', context)
    
    
#from collections import OrderedDict



# @login_required
# def emp_document(request):

#     # =========================
#     # GET LOGGED IN EMPLOYEE
#     # =========================
#     employee = Employee.objects.filter(
#         user=request.user
#     ).first()

#     if not employee:
#         messages.error(request, "Employee profile not found.")
#         return redirect('home')

#     # =========================
#     # CHECK ADMIN
#     # =========================
#     is_admin = False

#     if employee.employee_name:
#         is_admin = employee.employee_name.lower() == "admin"

#     # =========================
#     # ROLE BASED FOLDERS
#     # =========================
#     if is_admin:

#         # ADMIN SEE ALL EMPLOYEE FOLDERS
#         folders = EmpFolder.objects.select_related(
#             'employee'
#         ).order_by(
#             'employee__employee_name',
#             '-id'
#         )

#     else:

#         # NORMAL USER SEE ONLY OWN
#         folders = EmpFolder.objects.filter(
#             employee=employee
#         ).select_related(
#             'employee'
#         ).order_by('-id')

#     # =========================
#     # CREATE FOLDER
#     # =========================
#     if request.method == 'POST':

#         folder_form = EmpFolderForm(request.POST)

#         if folder_form.is_valid():

#             folder = folder_form.save(commit=False)

#             # ADMIN CAN CREATE FOR ANY EMPLOYEE
#             if is_admin:

#                 emp_id = request.POST.get('employee')

#                 if emp_id:
#                     folder.employee_id = emp_id
#                 else:
#                     folder.employee = employee

#             # NORMAL USER CREATE OWN FOLDER
#             else:

#                 folder.employee = employee

#             folder.save()

#             messages.success(
#                 request,
#                 "Folder created successfully."
#             )

#             return redirect('emp_document')

#     else:

#         folder_form = EmpFolderForm()

#         # NORMAL USER
#         if not is_admin:

#             folder_form.fields['employee'].queryset = Employee.objects.filter(
#                 id=employee.id
#             )

#             folder_form.fields['employee'].initial = employee
#             folder_form.fields['employee'].disabled = True

#     # =========================
#     # GROUP BY EMPLOYEE NAME
#     # =========================
#     grouped_folders = OrderedDict()

#     # ADMIN = SHOW ALL EMPLOYEE FOLDERS
#     if is_admin:

#         for folder in folders:

#             emp_name = (
#                 folder.employee.employee_name
#                 if folder.employee
#                 else "Unknown"
#             )

#             grouped_folders.setdefault(
#                 emp_name,
#                 []
#             ).append(folder)

#     # NORMAL USER = ONLY OWN FOLDERS
#     else:

#         grouped_folders[employee.employee_name] = list(
#             folders
#         )

#     # =========================
#     # CONTEXT
#     # =========================
#     context = {
#         'grouped_folders': grouped_folders,
#         'folder_form': folder_form,
#         'employee': employee,
#         'is_admin': is_admin,
#     }

#     return render(
#         request,
#         'documents/emp_display_file.html',
#         context
#     )
    
    
# =========================================================
# EMPLOYEE PAGE
# =========================================================

# @login_required
# def emp_page(request, folder_id):

#     folder = get_object_or_404(EmpFolder, id=folder_id)

#     employee = Employee.objects.filter(user=request.user).first()

#     # =====================================================
#     # SECURITY
#     # =====================================================
#     if not request.user.is_superuser:

#         if folder.employee != employee:
#             messages.error(request, "Permission denied.")
#             return redirect('emp_document')

#     # =====================================================
#     # FILES
#     # =====================================================
#     files = EmpFile.objects.filter(folder=folder).order_by('-id')

#     # =====================================================
#     # UPLOAD FILE
#     # =====================================================
#     if request.method == 'POST':

#         file_form = EmpFileForm(request.POST, request.FILES)

#         if file_form.is_valid():

#             file_obj = file_form.save(commit=False)

#             file_obj.folder = folder

#             # Employee assign
#             if request.user.is_superuser:
#                 file_obj.employee = folder.employee
#             else:
#                 file_obj.employee = employee

#             # File name auto
#             if not file_obj.name:
#                 file_obj.name = request.FILES['file'].name

#             file_obj.save()

#             messages.success(request, "File uploaded successfully.")

#             return redirect('emp_page', folder_id=folder.id)

#     else:
#         file_form = EmpFileForm()

#     context = {
#         'folder': folder,
#         'files': files,
#         'file_form': file_form,
#         'employee': employee,
#     }

#     return render(request, 'documents/emp_page.html', context)




@login_required
def emp_page(request, folder_id):
    folder = get_object_or_404(EmpFolder, id=folder_id)
    employee = Employee.objects.filter(user=request.user).first()
    is_admin = employee.employee_name.lower() == "admin" if employee.employee_name else False

    # Security Check
    if not request.user.is_superuser and not is_admin:
        if folder.employee != employee:
            messages.error(request, "Permission denied.")
            return redirect('emp_document')

    # Get components inside this folder
    subfolders = folder.subfolders.all().order_by('-id')
    files = EmpFile.objects.filter(folder=folder).order_by('-id')

    # Handle Forms based on what is submitted
    file_form = EmpFileForm()
    subfolder_form = EmpFolderForm(initial={'parent': folder, 'employee': folder.employee})

    if request.method == 'POST':
        # SUBFOLDER CREATION
        if 'create_subfolder' in request.POST:
            subfolder_form = EmpFolderForm(request.POST)
            if subfolder_form.is_valid():
                new_subfolder = subfolder_form.save(commit=False)
                new_subfolder.parent = folder
                new_subfolder.employee = folder.employee
                new_subfolder.save()
                messages.success(request, "Subfolder created successfully.")
                return redirect('emp_page', folder_id=folder.id)

        # FILE UPLOAD
        elif 'upload_file' in request.POST:
            file_form = EmpFileForm(request.POST, request.FILES)
            if file_form.is_valid():
                file_obj = file_form.save(commit=False)
                file_obj.folder = folder
                file_obj.employee = folder.employee
                if not file_obj.name:
                    file_obj.name = request.FILES['file'].name
                file_obj.save()
                messages.success(request, "File uploaded successfully.")
                return redirect('emp_page', folder_id=folder.id)

    context = {
        'folder': folder,
        'subfolders': subfolders,
        'files': files,
        'file_form': file_form,
        'subfolder_form': subfolder_form,
        'employee': employee,
        'is_admin': is_admin,
    }
    return render(request, 'documents/emp_page.html', context)
    


@login_required
def emp_move_folder(request, folder_id):
    employee = Employee.objects.filter(user=request.user).first()
    is_admin = employee.employee_name.lower() == "admin" if employee.employee_name else False
    
    if not is_admin:
        return JsonResponse({'success': False, 'error': 'Permission Denied'}, status=403)

    folder = get_object_or_404(EmpFolder, id=folder_id)
    if request.method == 'POST':
        target_id = request.POST.get('target_folder_id')
        if target_id == 'root' or not target_id:
            folder.parent = None
        else:
            if int(target_id) == folder.id:
                return JsonResponse({'success': False, 'error': 'Cannot move a folder into itself.'})
            target_folder = get_object_or_404(EmpFolder, id=target_id)
            folder.parent = target_folder
            
        folder.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})



@login_required
def emp_move_file(request, file_id):
    employee = Employee.objects.filter(user=request.user).first()
    is_admin = employee.employee_name.lower() == "admin" if employee.employee_name else False
    
    if not is_admin:
        return JsonResponse({'success': False, 'error': 'Permission Denied'}, status=403)

    file_obj = get_object_or_404(EmpFile, id=file_id)
    if request.method == 'POST':
        target_id = request.POST.get('target_folder_id')
        if target_id and target_id != 'root':
            target_folder = get_object_or_404(EmpFolder, id=target_id)
            file_obj.folder = target_folder
            file_obj.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Files must belong to a folder.'})
            
    return JsonResponse({'success': False})

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