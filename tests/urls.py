from django.urls import path

import allianceauth.urls

from . import views
from . import test_views

urlpatterns = allianceauth.urls.urlpatterns

urlpatterns += [
    # Navhelper test urls
    path("test-page/", views.page, name="p1"),
    path("test-view/", test_views.test_views, name="test_views"),
]
