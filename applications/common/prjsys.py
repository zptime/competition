# coding=utf-8
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)


def api_common_build_frontapp(request, yourname):
    if not check_coder(yourname):
        raise Exception(u'请通过api网站调用!')
    prjpath = os.path.join(settings.BASE_DIR, '..')
    output = os.popen('cd %s ; . ./buildfrontapp.sh %s' % (prjpath, yourname))
    result = output.read()  # .decode('GB2312').encode('utf8').splitlines()
    result = result.splitlines()
    return result


def check_coder(yourname):
    # 增加入参检查，执行命令比较危险，不检查的话有安全漏洞。
    if yourname in [u'余璐', u'王若舟', u'杜晶', u'杨杰', u'张翩', u'周司珺', u'陈曦', u'潘光', u'刘凯', u'其它']:
        return True
    else:
        return False


def api_common_build_frontresult(request):
    result = ''
    resultpath = os.path.join(settings.BASE_DIR, '..', 'buildfrontapp.log')
    if not os.path.exists(resultpath):
        return u"还没有人编译过呢!\n请先编译再查看结果!".splitlines()

    with open(resultpath, 'r') as f:
        result = f.read()

    result = result.splitlines()
    return result


def api_common_build_unlock(request):
    buildlock_path = os.path.join(settings.BASE_DIR, '..', 'buildlock')
    buildfinishlock_path = os.path.join(settings.BASE_DIR, '..', 'buildfinishlock')
    if os.path.exists(buildlock_path):
        os.remove(buildlock_path)
    if os.path.exists(buildfinishlock_path):
        os.remove(buildfinishlock_path)

    return u'删除成功'


