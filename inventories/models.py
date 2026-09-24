from django.db import models
from projects.models import ProjectFirstLevelName,Suppliers
from hrm.models import Employee
from purchase.models import HeadOfRequisition
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone


class Inventories(models.Model):
    requi_id = models.IntegerField(null=True, blank=True) 
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    employee_name = models.ForeignKey(Employee, on_delete=models.CASCADE)    
    item_name = models.ForeignKey(HeadOfRequisition, on_delete=models.CASCADE)
    vendor_name = models.ForeignKey(Suppliers, on_delete=models.CASCADE, null=True, blank=True)
    unit = models.CharField(max_length=100)
    qty = models.PositiveIntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, default=0)
    remark = models.TextField(blank=True, null=True)    
    approv_note = models.TextField(blank=True, null=True)    
    approv_acct_note = models.TextField(blank=True, null=True)
    approv_purch_note = models.TextField(blank=True, null=True)
    requisition_date = models.DateField(null=True, blank=True)
    qtysub = models.PositiveIntegerField(default=0)
    purch_id = models.IntegerField(null=True, blank=True) 
    purch_date = models.DateField(null=True, blank=True)
    purch_file_1 = models.ImageField(upload_to='purchase_docs/', blank=True, null=True)
    purch_file_2 = models.ImageField(upload_to='purchase_docs/', blank=True, null=True)
    purch_file_3 = models.ImageField(upload_to='purchase_docs/', blank=True, null=True)


    # def save(self, *args, **kwargs):
    #     if self.qty and self.rate:
    #         self.amount = self.qty * self.rate
    #     else:
    #         self.amount = 0
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.purch_id} - {self.project_name} - {self.item_name} - {self.vendor_name} - {self.requisition_date} - {self.amount} - {self.remark}"


class InventoryUse(models.Model):
    project_name = models.ForeignKey(ProjectFirstLevelName, on_delete=models.CASCADE)
    item_name = models.ForeignKey(HeadOfRequisition, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField()
    total_qty = models.PositiveIntegerField(default=0)
    qtysub_qty = models.PositiveIntegerField(default=0)
    details = models.TextField(blank=True, null=True)
    use_date = models.DateField(default=timezone.now)
    remark = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        from .models import Inventories  

        remaining_qty = self.qty
        
        inventories = Inventories.objects.filter(
            item_name=self.item_name,
            qtysub__gt=0
        )

        total_available = sum(inv.qtysub for inv in inventories)        
        if total_available < self.qty:
            raise ValidationError("Your use item qty exceeds the available stock item qty.")        
        with transaction.atomic():
            for inv in inventories:
                if remaining_qty <= 0:
                    break
                if inv.qtysub >= remaining_qty:
                    inv.qtysub -= remaining_qty
                    inv.save()
                    remaining_qty = 0
                else:
                    remaining_qty -= inv.qtysub
                    inv.qtysub = 0
                    inv.save()            
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_name} - {self.item_name} - {self.qty}"
        
        

from django.contrib.auth.models import User  

class DeletedRecord(models.Model):
    model_name = models.CharField(max_length=100)
    deleted_data = models.JSONField()
    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.model_name} deleted by {self.deleted_by} at {self.deleted_at}"
