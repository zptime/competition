# -*- coding=utf-8 -*-

import os

# 竞赛网25
SYSTEM_CODE = '25'

DB_ADMIN = 'root'

# 本系统包含的对外服务
SYSTEM_NAME = 'competition_v3'
SYSTEM_SERVICES = (SYSTEM_NAME,)

SECRET_KEY = '0f$@gun=@7es+9t%m%u7xl$g&kqar$ptt-xpc99lkdn6j_fmjn'

WSGI_APPLICATION = SYSTEM_NAME + '.wsgi.application'

ROOT_URLCONF = SYSTEM_NAME + '.urls'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

TEMP_DIR = os.path.join(BASE_DIR, 'temp')
# EXCEL_EXPORT_PATH = os.path.join(TEMP_DIR, 'excelexport.xls')

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'), )

MEDIA_PATH_PUBLIC = 'media/public/'  # 公开的media文件
MEDIA_PATH_PROTECT = 'media/protected/'  # 私有的media文件

MEDIA_KEY_EXCEL = 'media/excel'
MEDIA_DIR_EXCEL = os.path.join(BASE_DIR, MEDIA_KEY_EXCEL)

AWS_S3_USE_SSL = False
from boto.s3.connection import OrdinaryCallingFormat
AWS_S3_CALLING_FORMAT = OrdinaryCallingFormat()

ALLOWED_HOSTS = ['*']

AUTH_USER_MODEL = 'user.Account'

INSTALLED_APPS = (
    'suit',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'applications.bizlog',
    'django_cas_ng',
    'applications.swagger',
    'applications.common',
    'applications.user',
    'competition_v3',
    'applications.upload_resumable',
    'applications.work',
    'applications.team',
    'applications.score',
    'applications.data',
    'applications.statistics',
    'applications.activity',
    'applications.expert',
    'applications.news',
    'applications.subjudge',
    'applications.weixinmp',
    'applications.convert_service_client',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'applications.bizlog.record.LogMiddleware',
)

# 本地认证结合CAS认证
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_cas_ng.backends.CASBackend',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.request',
            ],
        },
    },
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

SUIT_CONFIG = {
    'ADMIN_NAME': u'竞赛网系统SaaS数据管理',
    'HEADER_DATE_FORMAT': 'Y年 F j日 l',
    'HEADER_TIME_FORMAT': 'H:i',
    'LIST_PER_PAGE': 50,
    'MENU': (
        {'app': 'common', 'label': u'通用',},
        {'app': 'competition_v3', 'label': u'竞赛网',},
    )
}

LANGUAGE_CODE = 'zh-cn'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(name)s:%(lineno)d] [%(levelname)s] - %(message)s'
        },
    },
    'filters': {
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.join(BASE_DIR + '/log/', 'django.log'),
            'formatter': 'standard',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'django_command': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.join(BASE_DIR + '/log/', 'command.log'),
            'formatter': 'standard',
        },
        'django.db.backends_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.join(BASE_DIR + '/log/', 'db.log'),
            'formatter': 'standard',
        },
        'task_trace': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.join(BASE_DIR + '/log/', 'task.log'),
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
        },
        'applications': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
            'propagate': False
        },
        'django.request': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
            'propagate': False
        },
        'django_command': {
            'handlers': ['django_command', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'task_trace': {
            'handlers': ['task_trace', 'console'],
            'level': 'DEBUG',
            'propagate': False
        },

    }
}

LOG_CENTER = {
    'log': os.path.join(BASE_DIR + '/log/', 'django.log'),
    'system_code': 'competition_v3',
    'system_name': u'竞赛网',
    'domain': 'http://127.0.0.1:8001',
    'table': 'common_oper_log',
    'rotate_search': 1,
    'include': ('^/api/', '^/test/api/'),
    'exclude': ('^/api/$', '^/api/docs/$', ),
    'long_request': {
        'threshold': 1000 * 2,
        'report_include': ('*', ),
        'report_exclude': ('^/api/common/upload/image', ),
    },
    'head_record_length': -1,
    'request_record_length': -1,
    'response_record_length': -1,
}

# 会话过期时间1天，默认值2周过期（1209600）
SESSION_COOKIE_AGE = 1209600

# 自定义HTTP请求消息头，用于移动设备标识客户端用户类型与学校
HTTP_HEADER_CURRENT_USER_TYPE = 'CURRENT_USER_TYPE'

# 节假日外部查询接口地址
HOLIDAY_URL = 'http://www.easybots.cn/api/holiday.php?m=%s'

# upload_resumable
# TMP_DIR = os.path.join(BASE_DIR, 'tmp_file')
DATA_STORAGE_USE_S3 = True   # 是否采用S3对象存储
DATA_STORAGE_USE_S3_HOST_URL = False  # 若该参数为真，文件URL使用S3 HOST做为域名
DATA_STORAGE_USE_ABSOLUTE_URL = False  # 默认是否采用绝对地址
FILE_STORAGE_DIR_NAME = "media"
FILE_UPLOAD_TEMP_DIR = os.path.join(BASE_DIR, 'temp')

PASSWORD_CRYPT_KEY = "58560e24317140589770c1af3bb2905c"

DEFAULT_PASSWORD = "123456"

UNZIP_TASK_WORK_NUM = 2  # 同时处理解压任务的作品数量
VIDEO_CONVERT_TASK_WORK_NUM = 2  # 同时处理视频转换任务的作品数量
CHANGE_DOC_FORMAT_TASK_WORK_NUM = 2

# 短信相关
APPKEY_EASY = '6ec1b164f7e047b0faad4e8c1f5e0a82'
APPSECRET_EASY = 'f198afbb3955'
TEMPLATEID_EASY = 3032443

# ckeditor支持上传文件类型与大小
UPLOAD_IMAGE_EXTENSION = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".PNG", ".JPG", ".JPEG", ".GIF", ".BMP")
UPLOAD_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
UPLOAD_VOICE_EXTENSION = ('*',)   # 文章中暂不能上传音频
UPLOAD_VOICE_SIZE = 20 * 1024 * 1024  # 20MB
UPLOAD_VIDEO_EXTENSION = ('.mp4', '.mov', '.MP4', '.MOV',)
UPLOAD_VIDEO_SIZE = 1024 * 1024 * 1024  # 1024MB
UPLOAD_FILE_EXTENSION = (".png", ".jpg", ".jpeg", ".gif", ".bmp",
                         ".flv", ".swf", ".mkv", ".avi", ".rm", ".rmvb", ".mpeg", ".mpg", ".mov", ".wmv", ".mp4",
                         ".mp3", ".wav",
                         ".rar", ".zip", "7z",
                         ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf", ".txt", ".md", ".xml",
                         ".PNG", ".JPG", ".JPEG", ".GIF", ".BMP",
                         ".FLV", ".SWF", ".MKV", ".AVI", ".RM", ".RMVB", ".MPEG", ".MPG", ".MOV", ".WMV", ".MP4",
                         ".MP3", ".WAV",
                         ".RAR", ".ZIP", ".7Z",
                         ".DOC", ".DOCX", ".XLS", ".XLSX", ".PPT", ".PPTX", ".PDF", ".TXT", ".MD", ".XML")
UPLOAD_FILE_SIZE = 300 * 1024 * 1024  # 300MB
ARTICLE_IMAGE_TEMP = 'temp/%s/image/'  # 文章图片暂存
ARTICLE_FILE_TEMP = 'temp/%s/file/'   # 文章附件暂存
ARTICLE_VIDEO_TEMP = 'temp/%s/video/'   # 视频附件暂存

# 微信获取用户信息相关
# weixin_redirect_uri = 'http://lk.frp.lu8.win/redirect_uri/'
# app_domain = 'liukai.ngrok1.hbeducloud.com'
WEIXIN_REDIRECT_URI = '/wx/access_token'
WEIXIN_REDIRECT_URI_FH = '/wx/access_token_fh'
WEIXIN_REDIRECT_URI_FHLOGIN = '/wx/access_token_fhlogin'

WEIXIN_DEFINECODE_JS = 'js'
WEIXIN_DEFINECODE_FH = 'fh'

# 前端DEBUG模式, 1为打开，0为关闭
WEB_DEBUG_MOD = 0

DEFAULT_WORK_FILE_SIZE_MAX = 2048  # MB


# 配置导入的转码资源模块路径形如“teacher_source.apps.resource.models”
CONVERT_SERVICE_CLIENT_RESOURCE_PATH = "applications.work.models"
# 配置导入的转码资源表名称 形如“Resource”
CONVERT_SERVICE_CLIENT_RESOURCE_NAME = "WorkFileObj"

