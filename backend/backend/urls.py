from api.views import redirect_link
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
    path('<short_link>/', redirect_link, name='redirect_link'),
]
