# -*- coding=utf-8 -*-

from django.conf.urls import url

from applications.common.views import *

urlpatterns = [
    # url(r'^api/common/upload/image', api_upload_image),  # 图片上传
    url(r'^api/common/test$', api_common_test),  # 测试方法
    url(r'^api/common/build/frontapp$', api_common_build_frontapp),  # 编译前端
    url(r'^api/common/build/frontresult$', api_common_build_frontresult),  # 查看编译结果
    url(r'^api/common/build/unlock$', api_common_build_unlock),  # 解除编译锁定
]
