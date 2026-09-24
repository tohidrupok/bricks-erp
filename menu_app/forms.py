from django import forms

from .models import MenuItem


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            "title", "icon", "url_name", "parent",
            "permission", "users", "groups", "order", "is_active",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "icon": forms.TextInput(attrs={"class": "form-control"}),
            "url_name": forms.TextInput(attrs={"class": "form-control"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "permission": forms.TextInput(attrs={"class": "form-control"}),
            "users": forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
            "groups": forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned = super().clean()
        parent = cleaned.get("parent")
        if parent and self.instance.pk and parent.pk == self.instance.pk:
            raise forms.ValidationError("A menu item cannot be its own parent.")
        if parent and parent.parent_id:
            raise forms.ValidationError(
                "Menu only supports 2 levels — the selected parent is already a child item."
            )
        return cleaned
