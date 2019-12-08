# -*- coding: utf-8 -*-

import os
from django.conf import settings
from django.conf.urls import include, url, patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
]

urlpatterns += [
    url(r'^logout', RedirectView.as_view(url='/html/logout')),
    url(r'', include('applications.common.urls')),
    url(r'', include('applications.work.urls')),
    url(r'', include('applications.data.urls')),
    url(r'', include('applications.user.urls')),
    url(r'', include('applications.team.urls')),
    url(r'', include('applications.score.urls')),
    url(r'', include('applications.news.urls')),
    url(r'', include('applications.statistics.urls')),
    url(r'', include('applications.upload_resumable.urls')),
    url(r"", include('applications.expert.urls')),
    url(r'', include('applications.activity.urls')),
    url(r'', include('applications.weixinmp.urls')),
    url(r"", include('applications.subjudge.urls')),
    url(r"^convert_service", include('applications.convert_service_client.urls')),

]

# html page
urlpatterns += [
    url(r'', include(settings.SYSTEM_NAME + '.urls_html')),
]

# swagger
urlpatterns += patterns('applications.swagger.views',
    url(r'^api/$', 'api_index'),
    url(r'^api/docs/$', 'api_docs'),
)

# html page
urlpatterns += patterns('templates.html',
    # url(r'^html/login$', 'html_login'),
    # url(r'^html/locallogin$', 'html_locallogin'),
    # url(r'^html/logout$', 'html_logout'),

                        )

# page's favicon
urlpatterns += patterns('', (r'^favicon\.ico$', RedirectView.as_view(url='/static/favicon.ico')),)

urlpatterns += staticfiles_urlpatterns()   # static

urlpatterns += patterns('',
    url(r'^media/(?P<path>.*)$',
        'django.views.static.serve',
        {'document_root': os.path.join(settings.BASE_DIR, 'media'),}),
    )
