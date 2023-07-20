import debug_toolbar
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/admin/')),
    path('__debug__/', include(debug_toolbar.urls)),
]
