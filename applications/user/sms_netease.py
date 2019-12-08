# coding=utf-8
import hashlib
import httplib
import json
import random
import string

import time
import urllib

import datetime

from applications.upload_resumable.err_code import ERR_SUCCESS
from applications.user.models import VerifyCode
from competition_v3.settings.base import APPKEY_EASY, APPSECRET_EASY, TEMPLATEID_EASY
from utils.const_def import FLAG_NO, FLAG_YES


def send_message(mobile):
    def get_nonce(length):
        """
             get不可重复字符串
        """
        # 不可重复字符串
        random_str = ''.join(random.sample(string.ascii_letters, length))
        return random_str

    # get the current time str use timestamp
    def get_curtime_str():
        now = time.time()
        curtime = int(now)
        return str(curtime)

    # get the sha1 hexcode string : AppSecret + Nounce + Curtime
    def get_sha1_code(AppSecret, Nonce, Curtime):
        sha1obj = hashlib.sha1()
        sha1obj.update(AppSecret + Nonce + Curtime)
        sha1code = sha1obj.hexdigest()
        return sha1code

    if not mobile:
        raise Exception(u"电话号码不能为空")
    raw_query = VerifyCode.objects.filter(mobile=mobile, del_flag=FLAG_NO, IMCode_status=FLAG_YES)
    if not raw_query:
        raise Exception(u"错误请求")
    else:
        AppKey = APPKEY_EASY
        AppSecret = APPSECRET_EASY
        templateid = TEMPLATEID_EASY

        Nonce_16 = get_nonce(16)
        Curtime = get_curtime_str()
        CheckSum = get_sha1_code(AppSecret, Nonce_16, Curtime)

        data = {"mobile":mobile,
                "templateid":templateid,
                "codeLen":6,
                }

        data = urllib.urlencode(data)

        headers = {"AppKey":AppKey,
                   "Content-Type":'application/x-www-form-urlencoded',
                   "CurTime":Curtime,
                   "CheckSum":CheckSum,
                   "Nonce":Nonce_16,
                   }

        # get the verify code from remote
        conn = httplib.HTTPSConnection("api.netease.im")

        conn.request('POST', '/sms/sendcode.action', data, headers)
        r1 = conn.getresponse()
        data1 = r1.read()
        conn.close()
        data1 = json.loads(data1, 'utf-8')
        code = ''
        if data1['code']== 200:
            code = data1['obj']
            msg = data1['msg']

        raw_query.update(code=str(code), timestamp=Curtime, update_time=datetime.datetime.now())
        return dict(c=ERR_SUCCESS[0], m=ERR_SUCCESS[1], d=[])


def verify_messagecode(mobile, code, expire_time=None):
    if not mobile or not code:
        raise Exception(u"手机号/验证码不能为空")
    raw_query = VerifyCode.objects.filter(mobile=mobile, del_flag=FLAG_NO, IMCode_status=FLAG_YES).values_list("code", "timestamp")
    if not raw_query:
        raise Exception(u"请重新发送验证码")
    else:
        codedata = list(raw_query)[0]
        if expire_time:
            create_timestamp = int(codedata[1])
            curtime = time.time()
            timestamp = int(curtime)
            if create_timestamp + expire_time < timestamp:
                raise Exception(u'验证码超时')
        if codedata[0] == code:
            VerifyCode.objects.filter(mobile=mobile, del_flag=FLAG_NO, IMCode_status=FLAG_YES).update(code_status=FLAG_YES, update_time=datetime.datetime.now())
            return dict(c=ERR_SUCCESS[0], m=ERR_SUCCESS[1], d=[])
        else:
            raise Exception(u"验证码错误")


def del_messagecode(mobile):
    # 清空所有验证码
    VerifyCode.objects.filter(mobile=mobile, del_flag=FLAG_NO, code_status=FLAG_YES).update(del_flag=FLAG_YES, update_time=datetime.datetime.now())
    return True
