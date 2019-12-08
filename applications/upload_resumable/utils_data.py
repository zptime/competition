# coding=utf-8
import logging
import os
import random
import string
import uuid
import hashlib
import json
import re
import requests
import datetime

from django.conf import settings
from django.http import HttpResponse
from django_cas_ng.utils import get_service_url

from applications.upload_resumable.storage.storage import get_storage_obj

logger = logging.getLogger(__name__)

# time out
UPLOAD_LOCK_RUNNING_TIMEOUT_SECONDS = 60
UPLOAD_LOCK_FINISH_TIMEOUT_DAYS = 7

# part num
INITIATE_UPLOAD_PART_NUM = 0
COMPLETE_UPLOAD_PART_NUM = 99999999

# status
UPLOAD_STATUS_RUNNING = 1
UPLOAD_STATUS_FINISHED = 2

# acquire return code
UPLOAD_ACQUIRE_NOT_IDLE = 0
UPLOAD_ACQUIRE_RUNNING = 1
UPLOAD_ACQUIRE_FINISH = 2
UPLOAD_ACQUIRE_RUNNING_TIME_OUT = 3
UPLOAD_ACQUIRE_FINISH_TIME_OUT = 4

# 文件URL类型
FILE_URL_STYLE_RELATIVE = 1
FILE_URL_STYLE_ABSOLUTE_OUTSIDE = 2
FILE_URL_STYLE_ABSOLUTE_INSIDE = 3
FILE_URL_STYLE_ABSOLUTE_S3 = 4

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
SUPPORTED_FILE_TYPE = [FILE_TYPE_PDF, FILE_TYPE_MP4, FILE_TYPE_FLV, FILE_TYPE_SWF, FILE_TYPE_IMG, FILE_TYPE_DOC,
                       FILE_TYPE_PPT, FILE_TYPE_XLS, FILE_TYPE_ZIP, FILE_TYPE_MP3]

NOT_CLEAN_FILE_LIST = ["readme"]


def get_file_type(file_name, type_list=SUPPORTED_FILE_TYPE):
    ext = ""
    if len(file_name) < 2:
        return FILE_TYPE_UNKNOWN[0], ext
    ext = os.path.splitext(file_name)[-1].lower()
    for file_type in type_list:
        if ext in file_type[1]:
            return file_type[0], ext
    return FILE_TYPE_UNKNOWN[0], ext


def get_file_url(path, absolute=None, internet=True):
    """
    :param path: 不包含bucket_name或media，保存在FileObj中的url的原始路径
    :param abs: 是否返回包含域名的绝对地址
    :param internet: 是否返回外网地址，否则返回内网地址，abs为True时生效
    :return: 返回文件的url
    """

    url = ""
    if not path:
        return url
    path = get_storage_obj().get_relative_url(path)

    # 不包含该参数时采用系统配置
    if settings.DATA_STORAGE_USE_S3_HOST_URL and settings.DATA_STORAGE_USE_S3:  # 开发环境才使用该配置
        url = 'http://' + settings.AWS_S3_HOST + ":" + str(settings.AWS_S3_PORT) + path
    elif absolute and not internet and settings.DATA_STORAGE_USE_S3:  # 采用S3存储，获取内网下载地址
        url = 'http://' + settings.AWS_S3_HOST + ":" + str(settings.AWS_S3_PORT) + path
    elif absolute or (absolute is None and settings.DATA_STORAGE_USE_ABSOLUTE_URL):
        url = get_service_url(settings.SELF_APP, internet) + path
    else:
        url = path
    return url


def gen_random_name():
    return uuid.uuid4().hex


def gen_path(prefix='', suffix='.xlsx', dir_path=settings.TEMP_DIR):
    clean_overdue_files()
    random_num = uuid.uuid4().hex
    file_name = "%s%s%s" % (prefix, random_num, suffix)
    if len(dir_path) > 0:
        file_path = os.path.join(dir_path, file_name)
        return file_path
    else:
        return file_name


def get_new_file_name_with_suffix(file_name, suffix, ext=""):
    src_ext = os.path.splitext(file_name)[-1]
    if not ext:
        ext = src_ext
    dst_file_name = file_name[:-len(src_ext)] + suffix + ext
    return dst_file_name


def generate_file_md5(filepath, blocksize=2**20):
    m = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def md5sum(data):
    if isinstance(data, str):
        None
    elif isinstance(data, unicode):
        data = unicode.encode(data, "utf-8")
    else:
        raise Exception('Invalid filename')
    m2 = hashlib.md5()
    m2.update(data)
    return m2.hexdigest()


def gen_err_code_response(err_code):
    dict_resp = {"c": err_code[0], "m": err_code[1], "d": []}
    return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json", status=err_code[2])


def save_file(file_stream, save_path):
    with open(save_path, 'wb+') as w:
        for chunk in file_stream.chunks():
            w.write(chunk)


def convert_ueditor_content(content):
    ret_content = content
    pat = r'<img src="(.*?)"'
    res_list = re.findall(pat, content, re.M)
    for res in res_list:
        if res.startswith("http"):
            continue
        elif res.startswith('/'):
            i = res.find("/", 1)
            if i < 0:
                continue
            dst_url = get_file_url(res[i+1:], absolute=True)
            res = '"' + res + '"'
            dst_url = '"' + dst_url + '"'
            ret_content = ret_content.replace(res, dst_url)
    return ret_content


# 下载文件
def download_file(url, local_dir=settings.TEMP_DIR):
    local_filename = url.split('/')[-1]
    local_path = os.path.join(local_dir, local_filename)
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    if r.status_code != 200:
            # or r.headers.get('Content-Type') != 'binary/octet-stream':
        logger.error("download file error: %s" % url)
        return ""
    with open(local_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    if os.path.exists(local_path):
        return local_path
    else:
        logger.error("download file error: %s" % url)
        return ""


def clean_overdue_files(dir_path=settings.TEMP_DIR):
    try:
        now = datetime.datetime.now()
        due_date = now - datetime.timedelta(hours=settings.DATA_STORAGE_TMP_FILE_EXPIRED_HOURS)

        for parent, dirnames, filenames in os.walk(dir_path):
            # 三个参数：分别返回 1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
            for filename in filenames:
                if filename in NOT_CLEAN_FILE_LIST:
                    continue
                abs_file_path = os.path.join(parent, filename)
                if os.path.isfile(abs_file_path):
                    mtimestamp = os.path.getmtime(abs_file_path)
                    mtime = datetime.datetime.fromtimestamp(mtimestamp)
                    if mtime < due_date:
                        os.remove(abs_file_path)
                        logger.info("clean tmp file: %s" % abs_file_path)
    except Exception as ex:
        logging.exception("Clean files in %s with exception:%s" % (dir_path, ex))


def get_nonce(length):
    """
         get不可重复字符串
    """
    # 不可重复字符串
    random_str = ''.join(random.sample(string.ascii_letters, length))
    return random_str
