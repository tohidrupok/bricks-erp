from django.contrib import admin
from .models import BOQ, ProjectFirstLevelName,Donation, EmployeeCost, SafetyEquipment, BoQCategory,ExpenseCost,SiteSupervisor,Suppliers,ProjectLocation,BoRevisedItem,ContractorActivity,MaterialEntry
from .models import *
admin.site.register(BOQ)
admin.site.register(EmployeeCost)
admin.site.register(SafetyEquipment)
admin.site.register(BoQCategory)
admin.site.register(ExpenseCost)
admin.site.register(SiteSupervisor)
admin.site.register(Suppliers)
admin.site.register(ProjectLocation)
admin.site.register(BoRevisedItem)
admin.site.register(ContractorActivity)
admin.site.register(MaterialEntry)
admin.site.register(Donation)
admin.site.register(ProjectDocument)
admin.site.register(ProjectScheduleItem)
admin.site.register(ProjectSchedule)
@admin.register(ProjectFirstLevelName)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['project_first_name', 'project_start_date', 'project_end_date', 'project_duration']
