#!/usr/bin/env python
# coding=utf-8

ERR_SUCCESS = [0, u'完成']
ERR_REQUESTWAY = [40006, u'请求方式错误']
ERR_MODEL_NAME_ERR = [40025, u"模块名称不存在"]
ERR_LOGIN_FAIL = [40003, u'用户名或密码错误']
ERR_USER_NOTLOGGED = [40004, u'用户未登录']
ERR_USER_AUTH = [40005, u'用户权限不够']
ERR_ITEM_NOT_EXIST = [40007, u'记录不存在']
ERR_ACTION_NOT_SUPPORT = [40006, u'不支持的ACTION']

ERR_DATA_WRITE_ERR = [40041, u"写入文件错误"]
ERR_FILE_FORMAT_NOT_SUPPORTED = [40008, u'文件格式不支持']

# upload resumable err_code
UPLOAD_ERR_FILE_SUCCESS = [0, "file upload sccess", 200]
UPLOAD_ERR_FILE_EXIST = [0, "file have exist", 200]
UPLOAD_ERR_PART_SUCCESS = [1, "chunk upload success", 200]
UPLOAD_ERR_CHUNK_EXIST = [2, "chunk already exists", 200]
UPLOAD_ERR_COMPLETE_SUCCESS = [3, "complete success", 200]
UPLOAD_ERR_FILE_MD5_ERR_ERR = [40091, "file md5sum error", 500]

UPLOAD_ERR_CANNOT_LOCK_ERROR = [40081, "cannot get lock", 503]
UPLOAD_ERR_COMPLETE_UPLOAD_ERROR = [40082, "cannot get lock", 503]
UPLOAD_ERR_PART_UPLOAD_ERROR = [40083, "cannot get lock", 503]

UPLOAD_ERR_CHUNK_NOT_EXIST = [40090, "chunk not found", 404]
UPLOAD_ERR_NOT_KNOWN_ERR = [40091, "server internal error", 500]

