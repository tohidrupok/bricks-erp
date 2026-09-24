import json
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from inventories.models import DeletedRecord

def log_deleted_data(obj, user):
    """
    Save deleted model instance data safely into DeletedRecord model,
    including proper JSON serialization of dates, decimals, etc.
    """
    try:
        # Safely convert model instance to JSON-serializable dict
        data = json.loads(json.dumps(model_to_dict(obj), cls=DjangoJSONEncoder))

        DeletedRecord.objects.create(
            model_name=obj.__class__.__name__,
            deleted_data=data,
            deleted_by=user
        )
    except Exception as e:
        # Optional: Log error or raise
        print(f"[log_deleted_data ERROR] {obj}: {e}")
