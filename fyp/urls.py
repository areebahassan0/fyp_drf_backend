from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('complaints/', include('complaints.urls')),  # Keep this as it is
    path('admin/', admin.site.urls),
    path('api/user/', include('user.urls')),
    path('', views.home, name='home'),
    path('billing/', include('billing.urls')),
    path('chatbot/', include('chatbot.urls')),
]
