import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and response.status_code >= 400:
        view = context.get('view')
        view_name = type(view).__name__ if view else 'unknown'
        logger.warning(
            'API %s error in %s: %s',
            response.status_code,
            view_name,
            response.data,
        )

    # Keep original DRF response structure intact so frontend can rely on
    # standard fields (detail, non_field_errors, field-level errors, etc.)
    return response
