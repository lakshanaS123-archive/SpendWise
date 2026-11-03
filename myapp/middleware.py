import logging
import time
import uuid

logger = logging.getLogger("spendwise.requests")


class RequestLoggingMiddleware:
    """
    Structured request logging middleware that records:
    - Request method
    - Request path
    - Response status code
    - Response duration in ms
    - Correlation ID (X-Request-ID)
    - Client IP address

    Security: Strictly omits sensitive payloads, cookies, passwords,
    and financial details.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.correlation_id = correlation_id

        start_time = time.time()
        response = self.get_response(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Attach correlation ID to response headers
        response["X-Request-ID"] = correlation_id

        # Log request info cleanly without sensitive bodies or headers
        client_ip = (
            request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            or request.META.get("REMOTE_ADDR", "unknown")
        )

        logger.info(
            f"[{correlation_id}] {request.method} {request.path} -> "
            f"Status: {response.status_code} | Duration: {duration_ms}ms | IP: {client_ip}"
        )

        return response
