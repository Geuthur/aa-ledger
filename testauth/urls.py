# Django
from django.urls import include, path

# Alliance Auth
from allianceauth import urls

urlpatterns = [
    path("", include(urls)),
]

handler500 = "allianceauth.views.Generic500Redirect"
handler404 = "allianceauth.views.Generic404Redirect"
handler403 = "allianceauth.views.Generic403Redirect"
handler400 = "allianceauth.views.Generic400Redirect"
