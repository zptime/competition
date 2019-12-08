# coding=utf-8
import os
from django.conf import settings
from djproxy.views import HttpProxy
from django.conf.urls import url, patterns, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView


class ApiProxy(HttpProxy):
    # 后台测试环境地址
    base_url = 'http://test-jsv2.hbeducloud.com:8088/api/'


class DataProxy(HttpProxy):
    # 这个是样例，根据需要进行修改，例如需要增加用户中心接口时，可用
    base_url = 'http://test-jsv2.hbeducloud.com:8088/competition_v3_test/'


urlpatterns = [
    url(r'^api/(?P<url>..*)$', ApiProxy.as_view(), name='proxy'),
    url(r'^data/(?P<url>..*)$', DataProxy.as_view(), name='proxy'),
    url(r'^competition_v3_test/(?P<url>..*)$', DataProxy.as_view(), name='proxy'),
]

# swagger
urlpatterns += patterns('applications.swagger.views',
                        url(r'^api/$', 'api_index'),
                        )


# html page
urlpatterns += [
    url(r'', include(settings.SYSTEM_NAME + '.urls_html')),
]

# page's favicon
urlpatterns += patterns('', (r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),)

urlpatterns += staticfiles_urlpatterns()   # static

urlpatterns += patterns('',
                        url(r'^media/(?P<path>.*)$',
                            'django.views.static.serve',
                            {'document_root': os.path.join(settings.BASE_DIR, 'media'), }),
                        )
