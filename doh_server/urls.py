from django.urls import path
from doh_server.views import doh_request

urlpatterns = [
    path("dns-query", doh_request, name="doh_request"),
]
