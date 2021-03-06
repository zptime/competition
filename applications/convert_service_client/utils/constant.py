#!/usr/bin/env python
# coding=utf-8

# 时间格式
DATE_FORMAT_MONTH = 2
DATE_FORMAT_DAY = 3

SECONDS_PER_DAY = 86400

# 状态标志
DEL_FLAG_YES = 1
DEL_FLAG_NO = 0

FLAG_YES = 1
FLAG_NO = 0

# 任务状态
TASK_STATUS_NOT_PROCESS = (0, u"未处理")
TASK_STATUS_PROCESSING = (1, u"正在处理")
TASK_STATUS_PROCESSED_SUCCESS = (2, u"处理成功")
TASK_STATUS_PROCESSED_ERROR = (3, u"处理失败")
TASK_STATUS_CHOICE = (TASK_STATUS_NOT_PROCESS, TASK_STATUS_PROCESSING, TASK_STATUS_PROCESSED_SUCCESS, TASK_STATUS_PROCESSED_ERROR)
TASK_PROCESSING_TIMEOUT_MINUTES = 60


# 文件类型
FILE_TYPE_PDF = ["pdf", [".pdf"]]
FILE_TYPE_MP4 = ["mp4", [".mp4", ".avi", ".mov", ".wmv", ".mkv", ".ogg", ".mpeg", ".webm", ".3gp", ".mpg"]]
FILE_TYPE_FLV = ["flv", [".flv"]]
FILE_TYPE_SWF = ["swf", [".swf"]]
FILE_TYPE_IMG = ["img", [".jpg", ".jpeg", ".gif", ".png", ".bmp"]]
FILE_TYPE_DOC = ["doc", [".doc", ".docx"]]
FILE_TYPE_PPT = ["ppt", [".ppt", ".pptx"]]
FILE_TYPE_XLS = ["xls", [".xls", ".xlsx"]]
FILE_TYPE_ZIP = ["zip", [".zip", ".rar"]]
FILE_TYPE_MP3 = ["mp3", [".mp3", ".ogg", ".wav", ".m4a", ".wma", ".amr"]]
FILE_TYPE_UNKNOWN = ["unknown", []]
FILE_MULTI_TYPE_OGG = '.ogg'
SUPPORTED_FILE_TYPE = [FILE_TYPE_PDF, FILE_TYPE_MP4, FILE_TYPE_FLV, FILE_TYPE_SWF, FILE_TYPE_IMG, FILE_TYPE_DOC,
                       FILE_TYPE_PPT, FILE_TYPE_XLS, FILE_TYPE_ZIP, FILE_TYPE_MP3]
SUPPORTED_FILE_ALL = SUPPORTED_FILE_TYPE.append(FILE_TYPE_UNKNOWN)


# 教师资源可视化的权限类型列表
USER_CUR_TYPE_NONE = 0
USER_CUR_TYPE_STUDENT = 1
USER_CUR_TYPE_TEACHER = 2
USER_CUR_TYPE_PARENT = 4
TR_AVAILABLE_MASK_LIST = [USER_CUR_TYPE_NONE, USER_CUR_TYPE_STUDENT, USER_CUR_TYPE_TEACHER, USER_CUR_TYPE_PARENT,
                          USER_CUR_TYPE_STUDENT | USER_CUR_TYPE_TEACHER, USER_CUR_TYPE_STUDENT | USER_CUR_TYPE_PARENT,
                          USER_CUR_TYPE_TEACHER | USER_CUR_TYPE_PARENT, USER_CUR_TYPE_STUDENT | USER_CUR_TYPE_TEACHER |USER_CUR_TYPE_PARENT]

RESOURCE_CATEGORY_COURSEWARE = (0, u"课件")
RESOURCE_CATEGORY_MATERIAL = (1, u"课程素材")
RESOURCE_CATEGORY_EXERCISE = (2, u"习题")
RESOURCE_CATEGORY_TEACHING_PLAN = (3, u"教案")
RESOURCE_CATEGORY_STUDY_CASE = (4, u"学案")
RESOURCE_CATEGORY_OTHERS = (5, u"其他")

RESOURCE_CATEGORY_CHOICE = (RESOURCE_CATEGORY_COURSEWARE, RESOURCE_CATEGORY_MATERIAL, RESOURCE_CATEGORY_EXERCISE,
                            RESOURCE_CATEGORY_TEACHING_PLAN, RESOURCE_CATEGORY_STUDY_CASE, RESOURCE_CATEGORY_OTHERS)
PUBLIC_PERMISSION_CHOICE = ((0, u"私有"), (1, u"全校"), (2, u"校级共享"), (4, u"公共资源"))

# 用户角色
USER_ROLE_NOT_SET = 0
USER_ROLE_ADMIN = 1
USER_ROLE_NORMAL = 2

# 请求超时时间
REQUEST_CONNECTION_TIMEOUT_SECONDS = 30
