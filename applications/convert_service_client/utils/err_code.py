#!/usr/bin/env python
# coding=utf-8


ERR_SUCCESS = [0, u'完成']
ERR_PART_SUCCESS = [2, u'部分完成']
ERR_LOGIN_FAIL = [40003, u'用户名或密码错误']
ERR_USER_NOTLOGGED = [40004, u'用户未登录']
ERR_USER_AUTH = [40005, u'用户权限不够']
ERR_REQUESTWAY = [40006, u'请求方式错误']
ERR_ACTION_NOT_SUPPORT = [40006, u'不支持的ACTION']
ERR_USER_INFO = [40007, u'用户信息错误']
ERR_USER_FLAG = [40007, u'用户标识错误']
ERR_USER_INFO_INCOMPLETE = [40007, u'用户信息不完整']
ERR_FILE_FORMAT_NOT_SUPPORTED = [40008, u'文件格式不支持']
ERR_INTERNAL_ERROR = [40009, u'服务器内部错误']
ERR_USER_ALREADY_EXIST = [40010, u'用户已经存在']
ERR_USER_NOT_EXIST = [40012, u'用户不存在']

ERR_DATA_NOT_FOUND = [40040, u"找不到相关数据"]
ERR_DATA_EXISTS = [40041, u"数据已存在"]

# 数据接收错误
ERR_DATA_RECEIVE_FORMAT_ILLEGAL = [40051, u"数据格式错误"]
ERR_DATA_RECEIVE_NOT_MATCH = [40052, u"数据与源数据不匹配"]
