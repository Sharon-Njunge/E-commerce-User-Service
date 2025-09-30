from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    # Get the default DRF response first
    response = exception_handler(exc, context)

    if response is not None:
        # Preserve DRF's status code and headers
        custom_response = {
            "success": False,
            "error": {"type": exc.__class__.__name__, "details": response.data},
        }
        response.data = custom_response
        return response  # ✅ reuse original response (keeps status + headers)

    # Fallback for unhandled exceptions
    return Response(
        {
            "success": False,
            "error": {
                "type": "ServerError",
                "details": "An unexpected error occurred.",
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
