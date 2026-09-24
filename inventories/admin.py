from django.contrib import admin
from .models import Inventories,InventoryUse,DeletedRecord

admin.site.register(Inventories)
admin.site.register(InventoryUse)

from .models import DeletedRecord

@admin.register(DeletedRecord)
class DeletedRecordAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'deleted_by', 'deleted_at')
    readonly_fields = ('model_name', 'deleted_data', 'deleted_by', 'deleted_at') 