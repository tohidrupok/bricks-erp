from django.db import models
from django.conf import settings
from hrm.models import RdaEmployee

class EmployeeTask(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateField()
    project = models.ForeignKey('projects.ProjectFirstLevelName', on_delete=models.CASCADE)
    
    # Direct model link
    employee = models.ForeignKey(RdaEmployee, on_delete=models.CASCADE, null=True, related_name='assigned_tasks')

    # Task status metrics
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    attachment = models.FileField(upload_to='task_attachments/', blank=True, null=True)
    emp_attachment = models.FileField(upload_to='task_emp_attachments/', blank=True, null=True)

    # Employee completion feedback metrics 
    completion_note = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Tracks author and dates
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-deadline']

    def __str__(self):
        return f"{self.title} - {self.status}"