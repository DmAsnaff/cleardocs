from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def shallow_health(request):
    return JsonResponse({"status": "ok"})


def deep_health(request):
    checks = {}
    ok = True

    try:
        connection.ensure_connection()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = str(e)
        ok = False

    try:
        cache.set("health_check", "1", 5)
        cache.get("health_check")
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = str(e)
        ok = False

    status_code = 200 if ok else 503
    return JsonResponse({"status": "ok" if ok else "degraded", "checks": checks}, status=status_code)
