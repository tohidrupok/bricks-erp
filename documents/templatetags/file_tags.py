from django import template

register = template.Library()

@register.simple_tag
def file_links(file, title):
    """
    Given a file and its title, return the appropriate view and download links.
    """
    if file.name.endswith(".pdf"):
        view_link = f'<a href="{file.url}" target="_blank" class="mr-2 text-blue-500 hover:text-blue-700"><i class="fas fa-eye"></i> View PDF</a>'
        download_link = f'<a href="{file.url}" download="{title}.pdf" class="text-green-500 hover:text-green-700"><i class="fas fa-download"></i> Download PDF</a>'
        return f'{view_link} {download_link}'
    elif file.name.endswith(".docx") or file.name.endswith(".doc"):
        view_link = f'<a href="https://docs.google.com/gview?url={file.url|escape}&embedded=true" target="_blank" class="mr-2 text-blue-500 hover:text-blue-700"><i class="fas fa-eye"></i> View Document</a>'
        download_link = f'<a href="{file.url}" download="{title}.docx" class="text-green-500 hover:text-green-700"><i class="fas fa-download"></i> Download Word</a>'
        return f'{view_link} {download_link}'
    else:
        return '<span class="text-gray-500">Unsupported file type</span>'
