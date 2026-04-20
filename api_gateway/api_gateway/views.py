import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

api = "localhost"
USER_SERVICE_URL = f"http://{api}:3001"
POST_SERVICE_URL = f"http://{api}:3002"
AI_SERVICE_URL = f"http://{api}:3003"
NOTIFICATION_SERVICE_URL = f"http://{api}:3004"


def proxy_request(request, target_url):
    method = request.method
    headers = {key: value for key, value in request.headers.items()}
    headers.pop("Host", None)
    headers.pop("Content-Length", None)

    try:
        if method == "GET":
            resp = requests.get(target_url, headers=headers, params=request.GET)
        elif method in {"POST", "PUT", "PATCH"}:
            resp = requests.request(method, target_url, headers=headers, data=request.body)
        elif method == "DELETE":
            resp = requests.delete(target_url, headers=headers)
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)

        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type.lower():
            return JsonResponse(resp.json(), status=resp.status_code, safe=False)

        return HttpResponse(resp.content, status=resp.status_code, content_type=content_type or None)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def user_service(request, path=""):
    path = (path or "").lstrip("/")
    target_url = f"{USER_SERVICE_URL}/api/users/" + path
    return proxy_request(request, target_url)

@csrf_exempt
def post_service(request, path=""):
    path = (path or "").lstrip("/")
    target_url = f"{POST_SERVICE_URL}/api/posts/" + path
    return proxy_request(request, target_url)

@csrf_exempt
def ai_service(request, path=""):
    path = (path or "").lstrip("/")
    target_url = f"{AI_SERVICE_URL}/api/ai/" + path
    return proxy_request(request, target_url)

@csrf_exempt
def notification_service(request, path=""):
    path = (path or "").lstrip("/")
    target_url = f"{NOTIFICATION_SERVICE_URL}/api/notifications/" + path
    return proxy_request(request, target_url)