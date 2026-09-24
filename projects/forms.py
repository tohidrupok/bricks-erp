from django import forms
from decimal import Decimal
from .models import  ProjectLocation,BOQ,ProjectFirstLevelName, BoRevisedItem,EmployeeCost,SafetyEquipment,BoQCategory,ExpenseCost,SiteSupervisor,Suppliers,BoQType,ContractorActivity,MaterialEntry,Donation


# class BoQTypeForm(forms.ModelForm):
#     class Meta:
#         model = BoQType
#         fields = ['boq_type_name']
#         widgets = {
#             'boq_type_name': forms.TextInput(attrs={'class': 'form-input'}),
#         }
        

class BOQForm(forms.ModelForm):
    class Meta:
        model = BOQ
        fields = '__all__'
        widgets = {
            'project_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'category_type': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'category_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'supplier_name': forms.Select(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'item_name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'unit': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'qty': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'rate': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full border rounded px-3 py-2'}),
            'remark': forms.Textarea(attrs={'class': 'w-full border rounded px-3 py-2', 'rows': 3}),
        }
            
            

class ProjectLocationForm(forms.ModelForm):
    class Meta:
        model = ProjectLocation
        fields = ['location_name', 'area']
        widgets = {
            'location_name': forms.TextInput(attrs={'class': 'form-input'}),
            'area': forms.TextInput(attrs={'class': 'form-input'}),
        }

class ProjectFirstLevelNameForm(forms.ModelForm):

    class Meta:
        model = ProjectFirstLevelName

        fields = [
            'project_first_name',
            'location',
            'project_type',
            'project_owner',
            'project_start_month',
            'project_duration',
            'project_size_sq_ft',
            'number_of_units',
            'number_of_floors',
            'units_per_floor',
            'soil_test_completed',
            'drawing_test_completed',
            'agreement_completed',
            'soil_test',
            'drawing_test',
            'agreement_document',
        ]

        widgets = {
            'project_start_month': forms.TextInput(
                attrs={'placeholder': 'e.g. April 2025'}
            ),
            'project_duration': forms.NumberInput(
                attrs={'min': 1}
            ),
            'project_size_sq_ft': forms.NumberInput(
                attrs={'min': 1}
            ),
            'number_of_units': forms.NumberInput(
                attrs={'min': 1}
            ),
            'number_of_floors': forms.NumberInput(
                attrs={'min': 1}
            ),
            'units_per_floor': forms.NumberInput(
                attrs={'min': 1}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Temporarily optional
        self.fields['project_start_month'].required = False
        self.fields['project_duration'].required = False


from django import forms
from .models import (
    ProjectFirstLevelName,
    ProjectDocument,
    ProjectSchedule
)


class ProjectDocumentForm(forms.ModelForm):

    class Meta:
        model = ProjectDocument

        fields = [
            'document_type',
            'title',
            'document',
        ]

        widgets = {
            'document_type': forms.Select(
                attrs={
                    'class': 'w-full border rounded-lg p-2'
                }
            ),

            'title': forms.TextInput(
                attrs={
                    'class': 'w-full border rounded-lg p-2',
                    'placeholder': 'Document title'
                }
            ),

            'document': forms.ClearableFileInput(
                attrs={
                    'class': 'w-full border rounded-lg p-2'
                }
            ),
        }


class ProjectScheduleForm(forms.ModelForm):

    class Meta:
        model = ProjectSchedule

        fields = [
            'sub_structure',
            'super_structure',
            'finishing',
        ]

        widgets = {

            'sub_structure': forms.NumberInput(
                attrs={
                    'class': 'w-full border rounded-lg p-2',
                    'min': 0,
                    'placeholder': 'Months'
                }
            ),

            'super_structure': forms.NumberInput(
                attrs={
                    'class': 'w-full border rounded-lg p-2',
                    'min': 0,
                    'placeholder': 'Months'
                }
            ),

            'finishing': forms.NumberInput(
                attrs={
                    'class': 'w-full border rounded-lg p-2',
                    'min': 0,
                    'placeholder': 'Months'
                }
            ),
        }
        
from django import forms
from .models import ProjectScheduleItem


# class ProjectScheduleItemForm(forms.ModelForm):

#     class Meta:
#         model = ProjectScheduleItem

#         fields = [
#             'subject_name',
#             'start_date',
#             'end_date',
#             'schedule_type',
#         ]

#         widgets = {
#             'subject_name': forms.TextInput(attrs={
#                 'class': 'w-full border rounded-lg p-2',
#                 'placeholder': 'Subject Name'
#             }),

#             'start_date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'w-full border rounded-lg p-2'
#             }),

#             'end_date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'w-full border rounded-lg p-2'
#             }),

#             'schedule_type': forms.Select(attrs={
#                 'class': 'w-full border rounded-lg p-2'
#             }),
#         }


class ProjectScheduleItemForm(forms.ModelForm):

    class Meta:
        model = ProjectScheduleItem
        fields = [
            'subject_name',
            'start_date',
            'end_date',
            'actual_start_date',
            'actual_end_date',
            'schedule_type',
        ]

        widgets = {
            'subject_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 text-sm',
                'placeholder': 'Subject Name',
            }),

            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded-lg px-3 py-2 text-sm',
            }),

            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded-lg px-3 py-2 text-sm',
            }),

            'actual_start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded-lg px-3 py-2 text-sm',
            }),

            'actual_end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded-lg px-3 py-2 text-sm',
            }),

            'schedule_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 text-sm',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        actual_start = cleaned_data.get('actual_start_date')
        actual_end = cleaned_data.get('actual_end_date')

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError(
                'Scheduled end date cannot be before start date.'
            )

        if actual_start and actual_end and actual_end < actual_start:
            raise forms.ValidationError(
                'Actual end date cannot be before actual start date.'
            )

        return cleaned_data

    
            
# class BOQForm(forms.ModelForm):
#     class Meta:
#         model = BOQ
#         exclude = ['status_item', 'update_item']
#         widgets = {
#             'project_name': forms.Select(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary dark:bg-darkmode-800 dark:border-transparent dark:text-white'
#             }),
#             'category_type': forms.TextInput(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm',
#                 'placeholder': 'Enter or select category type',
#             }),
#             'type_name': forms.TextInput(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm',
#                 'placeholder': 'Enter the category name',
#             }),
#             'category_name': forms.TextInput(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm',
#                 'placeholder': 'Enter the category name',
#             }),
#             'supplier_name': forms.Select(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm focus:ring-4 focus:ring-primary focus:ring-opacity-20 focus:border-primary dark:bg-darkmode-800 dark:border-transparent dark:text-white'
#             }),
#             'item_name': forms.TextInput(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm',
#                 'placeholder': 'Enter the item name',
#             }),
#             'unit': forms.TextInput(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm',
#                 'placeholder': 'Enter unit',
#             }),
#             'qty': forms.NumberInput(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm',
#                 'step': '0.01',
#                 'min': '0',
#                 'placeholder': 'Enter quantity',
#             }),
#             'rate': forms.NumberInput(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm',
#                 'step': '0.01',
#                 'min': '0',
#                 'placeholder': 'Enter rate',
#             }),
#             'amount': forms.NumberInput(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm',
#                 'placeholder': 'Enter amount',
#             }),
#             'remark': forms.Textarea(attrs={
#                 'class': 'w-full px-3 py-2 border rounded-md text-sm shadow-sm',
#                 'rows': 3,
#                 'placeholder': 'Optional remarks...',
#             }),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['category_type'].required = False  
#         if hasattr(self.fields['category_type'], 'choices'):
#             self.fields['category_type'].choices = []

#     def clean(self):
#         cleaned_data = super().clean()
#         qty = cleaned_data.get("qty")
#         rate = cleaned_data.get("rate")

#         if qty is None or rate is None:
#             raise forms.ValidationError("Quantity and Rate cannot be empty.")

#         try:
#             if Decimal(qty) <= 0 or Decimal(rate) <= 0:
#                 raise forms.ValidationError("Quantity and Rate must be greater than zero.")
#         except InvalidOperation:
#             raise forms.ValidationError("Invalid decimal value provided.")

#         return cleaned_data
        
        

class BOQForm(forms.ModelForm):
    class Meta:
        model = BOQ
        exclude = ['status_item', 'update_item', 'type_name', 'category_type']
        widgets = {
            'project_name': forms.Select(attrs={'class': 'your-css-class'}),
            'category_name': forms.TextInput(attrs={'class': 'your-css-class'}),
            'supplier_name': forms.Select(attrs={'class': 'your-css-class'}),
            'item_name': forms.TextInput(attrs={'class': 'your-css-class'}),
            'unit': forms.TextInput(attrs={'class': 'your-css-class'}),
            'qty': forms.NumberInput(attrs={'class': 'your-css-class'}),
            'rate': forms.NumberInput(attrs={'class': 'your-css-class'}),
            'amount': forms.NumberInput(attrs={'class': 'your-css-class'}),
            'remark': forms.Textarea(attrs={'class': 'your-css-class'}),
            'boq_date': forms.DateInput(attrs={'type': 'date', 'class': 'your-css-class'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        qty = cleaned_data.get("qty")
        rate = cleaned_data.get("rate")

        if qty is None or rate is None:
            raise forms.ValidationError("Quantity and Rate cannot be empty.")

        try:
            if Decimal(qty) <= 0 or Decimal(rate) <= 0:
                raise forms.ValidationError("Quantity and Rate must be greater than zero.")
        except InvalidOperation:
            raise forms.ValidationError("Invalid decimal value provided.")

        return cleaned_data
        
        
        
        

class BoRevisedItemForm(forms.ModelForm):
    class Meta:
        model = BoRevisedItem
        fields = ['category_name', 'item_name', 'unit', 'qty', 'rate']
        widgets = {
            'qty': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
        
# class BOQForm(forms.ModelForm):
#     class Meta:
#         model = BOQ
#         fields = '__all__'

#     def clean(self):
#         cleaned_data = super().clean()
#         qty = cleaned_data.get("qty")
#         rate = cleaned_data.get("rate")

#         if qty is None or rate is None:
#             raise forms.ValidationError("Quantity and Rate cannot be empty.")

#         if qty <= 0 or rate <= 0:
#             raise forms.ValidationError("Quantity and Rate must be greater than zero.")
        
        
        
# class EmployeeCostForm(forms.ModelForm):
#     class Meta:
#         model = EmployeeCost
#         fields = '__all__'

class EmployeeCostForm(forms.ModelForm):
    class Meta:
        model = EmployeeCost
        fields = [
            'project_name',
            'employee_name',
            'first_month_salary',
            'project_duration_months',
            'total_salary',
            'yearly_data'
        ]
        widgets = {
            'yearly_data': forms.Textarea(attrs={
                'rows': 4,
                'cols': 60,
                'placeholder': 'Example: [{"year": 2, "increment": 1000, "salary": 72000}]'
            }),
        }


class SafetyEquipmentForm(forms.ModelForm):
    class Meta:
        model = SafetyEquipment
        fields = ['project_name', 'item_name', 'quantity', 'item_cost', 'total_cost']


# class BoQCategoryForm(forms.ModelForm):
#     class Meta:
#         model = BoQCategory
#         fields = ['boq_cat_type','boq_cat_name']
#         labels = {
#             'boq_cat_name': 'BoQ Category Name',
#         }
#         widgets = {
#             'boq_cat_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Category Name'})
#         }




class BoQCategoryTypeForm(forms.ModelForm):
    class Meta:
        model = BoQCategory
        exclude = ['boq_cat_name'] 
        widgets = {
            'boq_cat_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Category Type Only',
            }),
        }

class BoQCategoryForm(forms.ModelForm):
    boq_cat_type = forms.ChoiceField(
        choices=[],  # will be set dynamically in view
        widget=forms.Select(attrs={
            'class': 'w-full text-sm border-slate-200 shadow-sm rounded-md placeholder:text-slate-400/90 focus:ring-4 focus:ring-blue-500 focus:border-blue-500 dark:bg-darkmode-800 dark:border-transparent dark:focus:ring-slate-700 dark:focus:ring-opacity-50'
        }),
        required=True,
        label="Category Type"
    )

    class Meta:
        model = BoQCategory
        fields = ['boq_cat_type', 'boq_cat_name']
        labels = {
            'boq_cat_name': 'BoQ Category Name',
        }
        widgets = {
            'boq_cat_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Category Name',
            }),
        }

        
        
        
class ExpenseCostForm(forms.ModelForm):
    class Meta:
        model = ExpenseCost
        fields = ['project_name', 'item_name', 'quantity', 'item_cost', 'total_cost']


class SiteSupervisorForm(forms.ModelForm):
    class Meta:
        model = SiteSupervisor
        fields = ['supervisor_name', 'address', 'phone', 'email', 'description', 'active']
        exclude=['total_amount','pay_amount']
        labels = {
            'supervisor_name': 'Contractor Name',
            'address': 'Contractor Address',
            'phone': 'Contractor Phone',
            'email': 'Contractor Email',
            'description': 'Contractor Description',
            'active': 'Contractor Active',
        }
        widgets = {
            'supervisor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Contractor Name'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Description', 'rows': 3}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class SuppliersForm(forms.ModelForm):
    class Meta:
        model = Suppliers
        fields = ['supplier_name', 'address', 'phone', 'email', 'description', 'active']
        exclude=['total_amount','pay_amount']
        labels = {
            'supplier_name': 'Supplier Name',
            'address': 'Supplier Address',
            'phone': 'Supplier Phone',
            'email': 'Supplier Email',
            'description': 'Supplier Description',
            'active': 'Supplier Active',
        }
        widgets = {
            'supplier_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Supplier Name'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Description', 'rows': 3}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        


class ContractorActivityForm(forms.ModelForm):
    class Meta:
        model = ContractorActivity
        fields = '__all__'
        widgets = {
            'create_date': forms.DateInput(attrs={'type': 'date', 'readonly': 'readonly'}),
            'work_start_date': forms.DateInput(attrs={'type': 'date'}),
            'work_end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        


class MaterialEntryForm(forms.ModelForm):
    class Meta:
        model = MaterialEntry
        fields = '__all__'  



class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['donation_name', 'address', 'phone', 'description', 'active']
        labels = {
            'donation_name': 'Donation Name',
            'address': 'Donation Address',
            'phone': 'Donation Phone',
            'description': 'Donation Description',
            'active': 'Donation Active',
        }
        widgets = {
            'donation_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Donation Name'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Phone Number'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Description', 'rows': 3}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        