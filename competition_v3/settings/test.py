# -*- coding=utf-8 -*-

from base import *

DEBUG = True

SYSTEM_DESC = u'竞赛网-测试'

LOGIN_URL='/html/login'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'competition_v3',
        'USER': 'admin',
        'PASSWORD': 'fhcloud86Fh12#$',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'CONN_MAX_AGE': 60,
        'OPTIONS': {'charset' : 'utf8mb4'},
    },
}


# 测试用本机domain，DEBUG模式下有效
DEBUG_TEST_DOMAIN = 'http://127.0.0.1:8000'   # 'http://127.0.0.1:80'

AWS_ACCESS_KEY_ID = "5NT2CU6KQE2Y34SGZTGT"
AWS_SECRET_ACCESS_KEY = "wfV2aMpXEiskrDnDPOoM1LU5ILgTJxMLdBDWBSIu"
AWS_STORAGE_BUCKET_NAME = "competition_v3_test"
AWS_S3_HOST = "192.168.200.100"
AWS_S3_PORT = 8000
USE_S3 = True

LOG_CENTER['domain'] = 'http://192.168.100.43:1785/api/internal/proxy'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'cache_01'
    }
}


# 配置当前需要转码服务的应用url,当应用不在用户中心时或者本机测试时可以使用,本地回送地址
CONVERT_SERVICE_CLIENT_APP_URL_CONF = "http://192.168.100.43:1385"

# 配置转码服务的url,远端服务器地址
CONVERT_SERVICE_SERVER_URL_CONF = "http://192.168.100.42:99"

# 是否开启子级评审功能
USE_SUBJUDGE = True

