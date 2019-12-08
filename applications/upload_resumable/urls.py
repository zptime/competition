
from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^api/upload/resumable$', ResumableUploadView.as_view()),
]
