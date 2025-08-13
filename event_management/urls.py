from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from scheduling.views import ProfileView, health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/profile/', ProfileView.as_view(), name='profile'),
    path('api/meetings/', include('scheduling.urls')),
    path('api/health-check/', health_check, name='health_check'),

    # Frontend Serving
    # This catch-all route serves the React index.html for any non-API, non-admin path.
    re_path(r'^.*', TemplateView.as_view(template_name='index.html')),
]
