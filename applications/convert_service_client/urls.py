from django.conf.urls import url
from views import *

urlpatterns = [
    url(r"^api/send_data$", api_convert_send_data),
    url(r"^api/receive_data$", api_convert_receive_data),
]
