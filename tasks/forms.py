from django import forms
from .models import EmployeeTask
from hrm.models import RdaEmployee


class EmployeeTaskForm(forms.ModelForm):

    deadline = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full border rounded-lg p-2 text-xs focus:ring focus:outline-none'
        })
    )

    employee = forms.ModelChoiceField(
        queryset=RdaEmployee.objects.all(),
        widget=forms.Select(attrs={
            'id': 'employeeSelect',
            'class': 'w-full border rounded-lg p-2 text-xs focus:ring focus:outline-none'
        }),
        required=True,
        empty_label="-- Select Employee --"
    )

    class Meta:
        model = EmployeeTask

        fields = [
            'project',
            'title',
            'description',
            'deadline',
            'attachment',
            'employee'
        ]

        widgets = {
            'project': forms.Select(attrs={
                'id': 'projectSelect',
                'class': 'w-full border rounded-lg p-2 text-xs focus:ring focus:outline-none'
            }),

            'title': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg p-2 text-xs focus:ring focus:outline-none',
                'placeholder': 'What needs to be done?'
            }),

            'description': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg p-2 text-xs focus:ring focus:outline-none',
                'rows': 3,
                'placeholder': 'Enter specific details about the assignment...'
            }),

            'attachment': forms.FileInput(attrs={
                'class': 'w-full text-xs text-slate-500'
            }),

            'emp_attachment': forms.FileInput(attrs={
                'class': 'w-full text-xs text-slate-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(EmployeeTaskForm, self).__init__(*args, **kwargs)

        self.fields['project'].empty_label = "-- Choose Project --"

        # Always show ALL employees
        self.fields['employee'].queryset = RdaEmployee.objects.all()