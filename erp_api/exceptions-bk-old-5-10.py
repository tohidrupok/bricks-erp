from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return Response({
            "404": "Error" if response.status_code == 404 else "Failed",
            "code": getattr(exc, 'default_code', 'error'),
            "messages": [
                {"message": str(exc)}
            ]
        }, status=response.status_code)

    return Response({
        "404": "Error",
        "code": "server_error",
        "messages": [
            {"message": str(exc)}
        ]
    }, status=getattr(exc, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR))
