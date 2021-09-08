"""theLapisDjango URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import debug_toolbar
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_jwt.views import refresh_jwt_token
from rest_framework_jwt.views import verify_jwt_token

urlpatterns = []

if settings.USE_STAFF:
    urlpatterns = urlpatterns + [    
        path("admin/", admin.site.urls),
    ]

if settings.USE_API:
    urlpatterns = urlpatterns + [
        path("api/", include("users.urls")),
        url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        url(r"^api/api-jwt-auth/$", obtain_jwt_token),  # JWT 토큰 획득
        url(r"^api/api-jwt-auth/refresh/$", refresh_jwt_token),  # JWT 토큰 갱신
        url(r"^api/api-jwt-auth/verify/$", verify_jwt_token),  # JWT 토큰 확인
        url(r"^api/rest-auth/", include("rest_auth.urls")),
        url(r"^api/rest-auth/registration/", include("rest_auth.registration.urls")),
    ]

urlpatterns = urlpatterns + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

if settings.DEBUG:
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
