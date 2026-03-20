from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    # Keep original DRF response structure intact so frontend can rely on
    # standard fields (detail, non_field_errors, field-level errors, etc.)
    return response
