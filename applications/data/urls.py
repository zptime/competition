# -*- coding=utf-8 -*-

from django.conf.urls import url

from applications.data.views import *


urlpatterns = [
    url(r'^api/upload/file$', api_upload_file),
    url(r'^api/delete/file$', api_delete_file),
    url(r'^api/list/file$', api_list_file),
    url(r'^api/ueditor/controller/$', api_ueditor_controller),
    url(r'^api/ckupload/', ckupload),
    url(r'^api/image/(?P<img>.+)', api_image),
]
