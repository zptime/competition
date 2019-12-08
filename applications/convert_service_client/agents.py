#!/usr/bin/env python
# coding=utf-8
import json
import logging
from django.db import transaction
from django.db.models import Q
from django.conf import settings
import requests
import traceback
import os

from models import *

# from ..user_center.models import Service
# from teacher_source.apps.resource.models import Resource
from ..upload_resumable.models import FileObj
# from ..data.utils import get_file_type, get_file_url
from ..data.agents import add_file

from utils.err_code import *
from utils.constant import *
from utils.public_fun import send_http_request, str_p_datetime, get_file_type, get_file_url

logger = logging.getLogger(__name__)

############################################################################
# 配置资源数据表

from conf import *

if settings.CONVERT_SERVICE_CLIENT_RESOURCE_PATH and settings.CONVERT_SERVICE_CLIENT_RESOURCE_NAME:
    im_module = __import__(settings.CONVERT_SERVICE_CLIENT_RESOURCE_PATH, globals(), locals(),
                           [settings.CONVERT_SERVICE_CLIENT_RESOURCE_NAME])
else:
    raise Exception(u"配置资源数据表项错误!")

Resource = getattr(im_module, settings.CONVERT_SERVICE_CLIENT_RESOURCE_NAME, None)
if not Resource:
    raise Exception(u"配置资源数据表项错误!")

if settings.CONVERT_SERVICE_CLIENT_APP_URL_CONF and settings.CONVERT_SERVICE_SERVER_URL_CONF:
    pass
else:
    from ..user_center.models import Service
    from ..user_center.agents import get_service_url

############################################################################

RECEIVE_API_URL_MAP = {"api_convert_receive_data": "convert_service/api/receive_data"}


def __get_file_obj_id(file_url):
    file_name = os.path.basename(file_url)
    try:
        result = add_file(user=None, file_name=file_name, file_url=file_url)
        if result["c"] != ERR_SUCCESS[0]:
            logger.info(u"fileobj对象创建失败[err_msg:{}]".format(result["m"]))
            file_obj_id = None
        else:
            file_obj_id = result['d'][0]["id"]
            logger.info(u"fileobj对象创建成功")
    except Exception as e:
        msg = traceback.format_exc()
        logger.info(u"fileobj对象创建失败[msg:{0}, trace_msg:{1}]".format(e.message, msg))
        file_obj_id = None
    return file_obj_id


@transaction.atomic
def process_receive_data(src_url, des_url, img_url, task_status, task_output, task_time):
    logger.debug(u'''receive a item[src_url-{0},des_url-{1},img_url-{2},task_status-{3},task_output-{4},
    task_time-{5}] from convert service'''.format(src_url, des_url, img_url, task_status, task_output, task_time))
    if not task_status or not src_url:
        logger.error(u"接收数据错误:{0}".format(ERR_DATA_RECEIVE_FORMAT_ILLEGAL[1]))
        return dict(c=ERR_DATA_RECEIVE_FORMAT_ILLEGAL[0], m=ERR_DATA_RECEIVE_FORMAT_ILLEGAL[1])
    convert_items = Resource.objects.filter(del_flag=DEL_FLAG_NO, src_file__url=src_url)
    if not convert_items:
        logger.error(u"接收数据匹配错误:{0}".format(ERR_DATA_RECEIVE_NOT_MATCH[1]))
        return dict(c=ERR_DATA_RECEIVE_NOT_MATCH[0], m=ERR_DATA_RECEIVE_NOT_MATCH[1])
    for convert_item in convert_items:
        task_status = int(task_status)
        if task_status == TASK_STATUS_PROCESSED_ERROR[0]:
            convert_item.task_status = task_status
            convert_item.task_output = task_output
            convert_item.task_time = str_p_datetime(task_time)
            convert_item.save()
        elif task_status == TASK_STATUS_PROCESSED_SUCCESS[0]:
            if not des_url or des_url == src_url:
                convert_item.des_file_id = convert_item.src_file_id
            else:
                file_type, ext = get_file_type(des_url)
                if convert_item.src_file.ext == FILE_MULTI_TYPE_OGG:
                    if file_type == FILE_TYPE_MP3[0]:
                        convert_item.src_file.type = FILE_TYPE_MP3[0]
                        convert_item.src_file.save()
                convert_item.des_file_id = __get_file_obj_id(des_url)
            if img_url == src_url:
                convert_item.img_file_id = convert_item.src_file_id
            elif img_url:
                convert_item.img_file_id = __get_file_obj_id(img_url)
            else:
                convert_item.img_file_id = convert_item.src_file_id
            convert_item.task_status = task_status
            convert_item.task_output = task_output
            convert_item.task_time = str_p_datetime(task_time)
            convert_item.save()
        else:
            pass
    logger.debug(u"数据接收成功，转码条目更新完成 :) ")
    return dict(c=ERR_SUCCESS[0], m=ERR_SUCCESS[1], d=[])


def convert_send_data(prefix="", host='', api_name='', obj_id=None):
    logger.debug(u"start sending data to convert service...")
    api_url = get_api_url(host, api_name)
    form_data = init_data(api_url, prefix, obj_id)
    if not form_data["src_info_list"]:
        logger.info(u"there is no data need to send to convert service!")
        return dict(c=ERR_DATA_NOT_FOUND[0], m=ERR_DATA_NOT_FOUND[1], d=[])
    try:
        service_api = get_convert_service_api()
        logger.debug(u"convert service api is {}, task begins".format(service_api))
        data_resp = send_http_request(url=service_api, form_data_dict=form_data)
        data_resp = json.loads(data_resp)
        if data_resp["c"] == ERR_SUCCESS[0]:
            logger.info(u"send data to convert service successfully")

        else:
            logger.error(u"send data error info, [error c: {c}, m: {m} ".format(**data_resp))
        return data_resp
    except Exception, e:
        str_error = traceback.format_exc()
        logger.error(str_error)
        raise e


def init_data(api_url="", prefix="", obj_id=None):
    if not obj_id:
        data_need_convert = Resource.objects.filter(del_flag=DEL_FLAG_NO, task_status=TASK_STATUS_NOT_PROCESS[0]).\
            exclude(Q(src_file__type=FILE_TYPE_UNKNOWN[0]) | Q(src_file__type=FILE_TYPE_ZIP[0])).\
            values("id", "src_file__url", "src_file__type", "src_file__ext")
    else:
        data_need_convert = Resource.objects.filter(del_flag=DEL_FLAG_NO, task_status=TASK_STATUS_NOT_PROCESS[0],
                                                    id=obj_id).\
            exclude(Q(src_file__type=FILE_TYPE_UNKNOWN[0]) | Q(src_file__type=FILE_TYPE_ZIP[0])).\
            values("id", "src_file__url", "src_file__type", "src_file__ext")
    data_need_convert = list(data_need_convert[:500])
    if not data_need_convert:
        logger.info(u"数据初始化完成:没有需要转换格式的数据")
        return dict(remote_url=api_url, src_info_list=[])
    data_list = []
    for item in data_need_convert:
        src_url = item["src_file__url"]
        file_type = item["src_file__type"]
        file_ext = item["src_file__ext"]
        if prefix:
            prefix = prefix
        else:
            component = src_url.split('/')
            if len(component) == 1:
                prefix = ""
            else:
                prefix = src_url[0:len(src_url)-len(component[-1])-1]
        src_url_handle = handle_file_url(src_url, absolute=True, internet=False, debug=True)
        dict_info = {"src_url": src_url_handle, "type": file_type,
                     "ext": file_ext, "prefix_dir": prefix}
        data_list.append(dict_info)
    data_list = json.dumps(data_list, ensure_ascii=False)
    return dict(remote_url=api_url, src_info_list=data_list)


def handle_file_url(src_url, absolute, internet, debug=False):
    if debug:
        if not settings.DATA_STORAGE_USE_S3:
            return settings.CONVERT_SERVICE_CLIENT_APP_URL_CONF + settings.MEDIA_URL + src_url
        else:
            return get_file_url(src_url, absolute=absolute, internet=internet)
    else:
        return get_file_url(src_url, absolute=absolute, internet=internet)


def get_api_url(host, api_name):
    if host:
        pass
    else:
        if settings.CONVERT_SERVICE_CLIENT_APP_URL_CONF:
            host = settings.CONVERT_SERVICE_CLIENT_APP_URL_CONF
        else:
            host = get_service_url(settings.SELF_APP, internet=False)
    api_name = api_name if api_name else RECEIVE_API_URL_MAP["api_convert_receive_data"]
    return host + "/" + api_name


def get_convert_service_api(host=None, convert_api=API_CONVERT_SERVICE_INIT_SERVICE):
    """
        获得转码服务的服务API接口
        @ para:
            host: 自定义的主机或者域名  none 返回默认的转码服务地址
            convert_api： 自定义的接口url

        @ return: 返回接口的url地址
    """
    if not host:
        if settings.CONVERT_SERVICE_SERVER_URL_CONF:
            return settings.CONVERT_SERVICE_SERVER_URL_CONF + convert_api
        else:
            convert_service = get_service_url(service_name=SERVICE_CONVERT_SERVICE, internet=False)
            if not convert_service:
                raise Exception(u"转码服务未定义")
            host = convert_service
            return host + convert_api
    else:
        return host + convert_api


def get_host_url(host=None, service_code=None):
    """
        获得本机的url地址，一般使用的是内网地址
        @ para:
            host: 自定义的本机ip或者域名
            service_code: 自定义的服务code
        @ return:
            返回服务的主机地址
    """
    if host:
        pass
    else:
        if settings.CONVERT_SERVICE_CLIENT_APP_URL_CONF:
            host = settings.CONVERT_SERVICE_CLIENT_APP_URL_CONF
        else:
            host = get_service_url(service_code, internet=False)
    return host


def query_to_server(query_form_data=None, server_api=None):
    """
        请求服务器端接口
        @ para:
            query_form_date: 自定义的本机地址，可测试使用
            server_api: 请求的服务器端api接口
        @ return:
            从服务器端拉取的数据
    """
    # 获取拉取的服务器端地址
    server_url = get_convert_service_api(host=None, convert_api=server_api)
    try:
        logger.debug(u"query convert service api is {}, task begins".format(server_url))
        data_resp = send_http_request(url=server_url, form_data_dict=query_form_data)
        logger.debug(u"query convert service success".format(server_url))
        data_resp = json.loads(data_resp)
        return data_resp
    except Exception, e:
        str_error = traceback.format_exc()
        logger.error(str_error)
        raise e


def pull_data_from_server(verbose=False):
    """
        从转码服务端拉取转码完成的数据
        @ para:
            verbose: 控制服务端数据的过滤，true时会重新传输没有下载完成的数据，否则只传输完成转码的一次请求
    """
    host_addr = get_host_url(service_code=settings.SELF_APP if 'SELF_APP' in dir(settings) else None)
    form_data = {"client_addr": host_addr, "verbose": int(verbose)}
    logger.info("pull data from server : the para is {}".format(form_data))
    result = query_to_server(query_form_data=form_data, server_api=API_CONVERT_SERVICE_PULL_DATA)
    if result["c"] != ERR_SUCCESS[0]:
        logger.error(u"pull data error info, [error c: {c}, m: {m} ".format(**result))
    else:
        logger.info(u"pull data from convert service successfully")
        data_result = result["d"]
        if not data_result:
            logger.info(u"pull data from convert service successfully,however it is empty! pass")
            return
        else:
            for item in data_result:
                src_url = item.get("src_url")
                des_url = item.get("des_url")
                img_url = item.get("img_url")
                task_status = item.get("task_status")
                task_output = item.get("task_output")
                task_time = item.get("task_time")
                # 系统使用的是s3共享存储时
                if settings.DATA_STORAGE_USE_S3:
                    logger.info("file system use s3 storage, process data directly")
                    process_receive_data(src_url, des_url, img_url, task_status, task_output, task_time)
                else:
                    logger.info("file system use local media storage, process data with additional models")
                    # 本地存储时使用的方法
                    process_item_local_storage(src_url, des_url, img_url, task_status, task_output, task_time)


def process_item_local_storage(src_url, des_url, img_url, task_status, task_output, task_time):
    """
        当使用本地存储时的数据处理方案--数据暂存

    """
    logger.debug(u'''receive a item[src_url-{0},des_url-{1},img_url-{2},task_status-{3},task_output-{4},
    task_time-{5}] from convert service'''.format(src_url, des_url, img_url, task_status, task_output, task_time))
    if not task_status or not src_url:
        logger.error(u"接收数据错误:{0}".format(ERR_DATA_RECEIVE_FORMAT_ILLEGAL[1]))
        return dict(c=ERR_DATA_RECEIVE_FORMAT_ILLEGAL[0], m=ERR_DATA_RECEIVE_FORMAT_ILLEGAL[1])
    convert_items = Resource.objects.filter(del_flag=DEL_FLAG_NO, src_file__url=src_url)
    if not convert_items:
        logger.error(u"接收数据匹配错误:{0}".format(ERR_DATA_RECEIVE_NOT_MATCH[1]))
        return dict(c=ERR_DATA_RECEIVE_NOT_MATCH[0], m=ERR_DATA_RECEIVE_NOT_MATCH[1])
    for convert_item in convert_items:
        task_status = int(task_status)
        if task_status == TASK_STATUS_PROCESSED_ERROR[0]:
            logger.info(u"处理服务端转码失败数据")
            convert_item.task_status = task_status
            convert_item.task_output = task_output
            convert_item.task_time = str_p_datetime(task_time)
            convert_item.save()
            logger.debug(u"数据接收成功，转码条目更新完成 :) ")
        else:
            logger.info(u"处理服务端转码成功数据")
            TmpStorage.objects.update_or_create(src_url=src_url, des_url=des_url, img_url=img_url)
            logger.debug(u"数据暂存成功 :) ")


def download_file_server():
    """
        从服务器端下载文件，并更新表
    """
    if settings.DATA_STORAGE_USE_S3:
        return
    while True:
        logger.info(u"下载循环开始...")
        storage_obj = TmpStorage.objects.filter(del_flag=FLAG_NO, download_status=TASK_STATUS_NOT_PROCESS[0]).first()
        if not storage_obj:
            logger.info(u"没有下载对象，下载循环结束。")
            return
        storage_obj.download_status = TASK_STATUS_PROCESSING[0]
        storage_obj.save()
        download_msg = ""
        convert_items = Resource.objects.filter(del_flag=DEL_FLAG_NO, src_file__url=storage_obj.src_url)
        src_file_id = convert_items.first().src_file_id
        # 不需要转码时
        if not storage_obj.des_url or storage_obj.des_url == storage_obj.src_url:
            logger.info(u"文件不需要转码,不用下载")
            convert_items.update(des_file_id=src_file_id)
        else:
            download_url = get_server_file_url(storage_obj.des_url)
            logger.info(u"下载转码文件url-{}".format(download_url))
            try:
                file_path = download_file_local(download_url, settings.MEDIA_ROOT, storage_obj.des_url)
                if not file_path:
                    logger.info(u"转码文件下载失败；")
                    download_msg += u"转码文件下载失败；"
                else:
                    logger.info(u"转码文件下载成功：）")
                    logger.info(u"新建fileobj数据库表项")
                    file_obj_id = __get_file_obj_id(storage_obj.des_url)

                    convert_items.update(des_file_id=file_obj_id)
                    logger.info(u"数据库表项建立，更新条目数据库成功:)")
            except:
                download_msg += u"下载转码文件时发生错误；"
                logger.info(u"下载转码文件时发生错误；")
        if not storage_obj.img_url or storage_obj.img_url == storage_obj.src_url:
            convert_items.update(img_file_id=src_file_id)
            logger.info(u"缩略文件不需要转码,不用下载")
        else:
            download_url = get_server_file_url(storage_obj.img_url)
            logger.info(u"下载缩略文件url{}".format(download_url))
            try:
                file_path = download_file_local(download_url, settings.MEDIA_ROOT, storage_obj.img_url)

                if not file_path:
                    download_msg += u"缩略图文件下载失败；"
                    logger.info(u"缩略图文件下载失败；")
                else:
                    logger.info(u"缩略图文件下载成功：）")
                    logger.info(u"新建fileobj数据库表项")
                    file_obj_id = __get_file_obj_id(storage_obj.img_url)
                    convert_items.update(img_file_id=file_obj_id)
                    logger.info(u"数据库表项建立，更新条目数据库成功:)")
            except:
                download_msg += u"下载缩略图文件时发生错误；"
                logger.info(u"下载缩略图文件时发生错误；")
        convert_items.update(task_status=TASK_STATUS_PROCESSED_SUCCESS[0], task_output=download_msg)
        storage_obj.download_status = TASK_STATUS_PROCESSED_SUCCESS[0]
        storage_obj.download_output = download_msg
        storage_obj.save()


def download_task():
    """
        下载的异步任务
    """
    if settings.DATA_STORAGE_USE_S3:
        return
    if TmpStorage.objects.filter(del_flag=FLAG_NO, download_status=TASK_STATUS_NOT_PROCESS[0]).exists():
        task_count = TmpStorage.objects.filter(del_flag=FLAG_NO, download_status=TASK_STATUS_PROCESSING[0]).count()
        if task_count <= 3:
            logger.info(u"开始下载服务器端转码文件。。。")
            download_file_server()
        else:
            return


def get_server_file_url(url):
    """
        获取文件的下载地址
    """
    server_url = get_convert_service_api(convert_api="")
    return server_url + settings.MEDIA_URL + url


def download_status_push():
    """
        下载状态的回送
    """
    if settings.DATA_STORAGE_USE_S3:
        return
    # TODO something
    client_download_done = TmpStorage.objects.filter(del_flag=FLAG_NO, download_status=TASK_STATUS_PROCESSED_SUCCESS[0],
                                                     transfer_status=TRANSFER_STATUS_INIT[0])
    if not client_download_done:
        logger.info(u"没有下载状态完成的任务需要推送到服务器")
        return
    data_info = client_download_done.values('src_url')
    data = []
    for item in data_info:
        src_url_handle = handle_file_url(item['src_url'], True, False, debug=True)
        dict_tmp = {"src_url": src_url_handle}
        data.append(dict_tmp)
    logger.info(u"数据源[{}]下载任务完成，推送服务器删除临时文件".format(data))
    form_data = {"src_info_list": json.dumps(data, ensure_ascii=False)}
    result = query_to_server(form_data, server_api=API_CONVERT_SERVICE_UPDATE_STATUS)
    if result['c'] != ERR_SUCCESS[0]:
        logger.error(u"下载状态的推送请求失败")
        client_download_done.update(transfer_status=TRANSFER_STATUS_FAILED[0])
    else:
        logger.info(u"下载状态的推送请求成功")
        client_download_done.update(transfer_status=TRANSFER_STATUS_SUCCESS[0])


def update_status_remote_task():
    """
        上传状态更新任务
    """
    download_status_push()


# 下载文件
def download_file_local(url, local_dir=settings.MEDIA_ROOT, file_name=None):
    if not file_name:
        local_filename = url.split('/')[-1]
        local_path = os.path.join(local_dir, local_filename)
    else:
        local_path = os.path.join(local_dir, file_name)
    # NOTE the stream=True parameter
    logger.info("begin download from [url:{0}] to [local_path: {1}] ".format(url, local_path))
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
        logger.info("download success")
        return local_path
    else:
        logger.error("download file error: %s" % url)
        return ""
