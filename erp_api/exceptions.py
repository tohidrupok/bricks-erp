from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Custom global exception handler for DRF.
    Returns a consistent response structure for all errors.
    """
    # Get default response from DRF (if available)
    response = exception_handler(exc, context)

    # If DRF has handled the exception
    if response is not None:
        code = str(response.status_code)
        message = response.data.get("detail", "An error occurred") if isinstance(response.data, dict) else "An error occurred"
        
        return Response({
            "code": code,
            "status": "Error" if response.status_code >= 400 else "Failed",
            "messages": [
                {"message": message}
            ]
        }, status=response.status_code)

    # If DRF did not handle it (unexpected exception)
    return Response({
        "code": "500",
        "status": "Error",
        "messages": [
            {"message": "Internal server error"}
        ]
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
