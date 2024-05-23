from django.urls import path

import allianceauth.urls

from . import views

urlpatterns = allianceauth.urls.urlpatterns

urlpatterns += [
    # Navhelper test urls
    path("test-page/", views.page, name="p1"),
    path("test-view/", views.test_settings, name="test_settings"),
]
