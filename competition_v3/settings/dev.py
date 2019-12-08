# -*- coding=utf-8 -*-

import platform

from base import *

DEBUG = True

SYSTEM_DESC = u'竞赛网-开发'

LOGIN_URL='/html/locallogin'

if 'Windows' in platform.platform():
    dbcharset = 'utf8'
else:
    dbcharset = 'utf8mb4'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'competition_v3',
        'USER': 'liukai',
        'PASSWORD': 'liukai',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {'charset': dbcharset},
    },
}


# 测试用本机domain，DEBUG模式下有效
DEBUG_TEST_DOMAIN = 'http://127.0.0.1:8000'   # 'http://127.0.0.1:80'

AWS_ACCESS_KEY_ID = "5NT2CU6KQE2Y34SGZTGT"
AWS_SECRET_ACCESS_KEY = "wfV2aMpXEiskrDnDPOoM1LU5ILgTJxMLdBDWBSIu"
AWS_STORAGE_BUCKET_NAME = "competition_v3_test"
AWS_S3_HOST = "127.0.0.1"
AWS_S3_PORT = 58000
USE_S3 = False

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'cache_01'
#     }
# }

REDIS_URL = '127.0.0.1:6379'
REDIS_PASSWD = ''   # no password
REDIS_LOCATION = 'redis://' + REDIS_URL + '/'
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_LOCATION + '0',   # distinguished by each environment
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 10,  # in seconds
            "SOCKET_TIMEOUT": 10,  # in seconds
            "IGNORE_EXCEPTIONS": True,
        }
    }
}


# 配置当前需要转码服务的应用url,当应用不在用户中心时或者本机测试时可以使用,本地回送地址
CONVERT_SERVICE_CLIENT_APP_URL_CONF = "http://127.0.0.1"

# 配置转码服务的url,远端服务器地址
CONVERT_SERVICE_SERVER_URL_CONF = "http://127.0.0.1"

# 是否开启子级评审功能
USE_SUBJUDGE = True


