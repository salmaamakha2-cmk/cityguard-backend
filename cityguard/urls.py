from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def api_root(request):
    html = """
    <html>
        <head>
            <title>CityGuard Backend</title>
            <style>
                body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f8fafc; }
                .card { background: white; padding: 2rem; border-radius: 1rem; shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); text-align: center; border: 1px solid #e2e8f0; }
                h1 { color: #0f172a; }
                p { color: #64748b; margin-bottom: 2rem; }
                .btn { background: #3b82f6; color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-decoration: none; font-weight: bold; transition: background 0.2s; }
                .btn:hover { background: #2563eb; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🚀 CityGuard Backend est EN LIGNE</h1>
                <p>Ceci est le serveur de données (Backend).<br>Pour voir votre <b>Dashboard Admin</b>, assurez-vous de lancer votre application React (npm run dev) :</p>
                <a href="http://localhost:5173" class="btn">ACCÉDER AU DASHBOARD (REACT)</a>
            </div>
        </body>
    </html>
    """
    return HttpResponse(html)

def api_info(request):
    return JsonResponse({
        "name": "CityGuard API",
        "version": "1.0",
        "status": "online",
        "endpoints": {
            "users": "/api/users/",
            "reports": "/api/reports/",
            "docs": "/swagger/"
        }
    })

schema_view = get_schema_view(
    openapi.Info(
        title="CityGuard API",
        default_version='v1',
        description="API de gestion des signalements urbains",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('favicon.ico', lambda x: HttpResponse(status=204)),
    path('api/', api_info, name='api-info'),
    path('api/users/', include('users.urls')),
    path('api/reports/', include('reports.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)