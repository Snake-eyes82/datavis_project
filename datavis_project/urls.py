"""
URL configuration for datavis_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
print("--- !!! EXECUTING MAIN URLS.PY !!! ---")
#datavis_project/main/urls.py
from django.contrib import admin
from django.urls import include, path
from django.conf import settings # Import settings
from django.conf.urls.static import static



urlpatterns = [

    path('', include('visualizer.urls')),
    path('admin/', admin.site.urls),
    #path('visualizer/', include('visualizer.urls')), # Keep this as well
    # ... other paths ...
]

# Serve static files during development (not recommended for production)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    pass
