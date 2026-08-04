"""
URL configuration for quick_order_dj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from quick_order_dj import settings
from django.conf.urls.static import static
from user_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.logIn, name='home'),
    path('login/', views.logIn, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.log_out, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/users/', views.users_settings, name='users_settings'),
    path('settings/users/create/', views.user_create, name='user_create'),
    path('settings/groups/', views.groups_settings, name='groups_settings'),
    path('settings/groups/create/', views.group_create, name='group_create'),
    path('', include('order_app.urls')),

]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
