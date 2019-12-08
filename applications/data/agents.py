# coding=utf-8
import json
from utils.public_fun import *
from utils.file_fun import *
from utils.const_def import *
from utils.const_err import *
from applications.work.models import Work
from django.conf import settings
from django.db.models import Q
from django.db import transaction
import os

from applications.upload_resumable.models import FileObj


def upload_file(user, file_obj, type_list=SUPPORTED_FILE_TYPE, activity_id=0, prefix="", cur_user_id=0):
    activity_id = int(activity_id)
    # user_id = 0
    # if user:
    #     user_id = user.id
    cur_user_id = cur_user_id if cur_user_id else 0
    file_name = file_obj.name
    file_size = file_obj.size

    # 计算md5,addby liukai
    # file_md5 = get_fileobj_md5(file_obj.file)

    file_type, ext = get_file_type(file_name, SUPPORTED_FILE_TYPE)
    if not file_type:
        if not type_list:  # 支持上传所有文件类型
            file_type = FILE_TYPE_UNKNOWN[0]
        else:
            return {"c": ERR_FILE_FORMAT_NOT_SUPPORTED[0], "m": ERR_FILE_FORMAT_NOT_SUPPORTED[1], "d": []}
    # save data
    remote_file_name = gen_s3_file_path(suffix=ext, abs=False)
    if prefix:
        remote_file_name = prefix + '/' + remote_file_name
    url = str(activity_id) + '/' + remote_file_name
    md5sum = get_object_storage_obj().upload_file_obj(file_obj, url)
    file_obj = FileObj.objects.create(name=file_name, url=url, size=file_size, type=file_type, ext=ext,
                                      uploader_id=user.id if user and user.is_authenticated() else 0, activity_id=activity_id,
                                      md5sum=md5sum)
    abs_url = get_image_url(url)
    ret_dict = {"id": file_obj.id, 'url': abs_url, 'type': file_type, 'size': file_size, "name": file_name}
    dict_resp = {"c": SUCCESS[0], "m": SUCCESS[1], "d": [ret_dict]}
    return dict_resp


def ueditor_controller(user, file_obj):
    return_info = {
        'url': "",            # 保存后的文件名称
        'original': "",        # 原始文件名
        'type': "",
        'state': "SUCCESS",    # 上传状态，成功时返回SUCCESS,其他任何值将原样返回至图片上传框中
        'size': 0
    }

    dict_resp = upload_file(user, file_obj)
    if dict_resp["c"] != SUCCESS[0]:
        return_info["state"] = ERR_DATA_WRITE_ERR[1]
        return return_info
    file_info = dict_resp["d"][0]
    return_info["url"] = file_info["url"]
    return_info["original"] = file_info["name"]
    return_info["type"] = file_info["type"]
    return_info["size"] = file_info["size"]
    return return_info


@transaction.atomic
def part_upload_complete(user, file_name, src_file_name, file_size, activity_id=0):
    file_type, ext = get_file_type(file_name)
    if not file_type:
        return {"c": ERR_FILE_FORMAT_NOT_SUPPORTED[0], "m": ERR_FILE_FORMAT_NOT_SUPPORTED[1], "d": []}

    url = file_name
    # file_obj = FileObj.objects.filter(name=src_file_name, url=url, size=file_size, type=file_type, ext=ext, uploader_id=user.id, del_flag=FALSE_INT).first()
    # if not file_obj:
    file_obj, created = FileObj.objects.update_or_create(name=src_file_name, url=url, size=file_size, type=file_type, ext=ext, uploader_id=user.id, activity_id=activity_id)
    abs_url = get_image_url(url)
    ret_dict = {"id": file_obj.id, 'url': abs_url, 'type': file_type, 'size': file_size, "name": src_file_name}
    dict_resp = {"c": SUCCESS[0], "m": SUCCESS[1], "d": [ret_dict]}
    return dict_resp


def list_file(account, user, activity_id, file_name="", work_id=""):
    # 查询所有我上传的，还没有关连到作品的文件。
    ret_file_list = []
    assigned_file_id_list = Work.objects.filter(uploader=user, del_flag=FALSE_INT).exclude(rar_file_id__isnull=True)\
        .values_list("rar_file_id", flat=True)
    file_obj_list = FileObj.objects.filter(uploader_id=account.id, type=FILE_TYPE_ZIP[0], activity_id=activity_id,
                                           del_flag=FALSE_INT).exclude(id__in=assigned_file_id_list)
    if file_name:
        file_obj_list.filter(name__contains=file_name)
    # if work_id:
    #     work_obj = Work.objects.filter(id=int(work_id))
    #     author_name = work_obj.authors.split("/")[0]
    #     file_obj_list.filter(Q(name__contains=work_obj.name) | Q(name__contains=author_name))
    file_obj_list = file_obj_list.values()
    for i, file_obj in enumerate(file_obj_list):
        ret_file = {"id": file_obj["id"], "name": file_obj["name"], "url": get_image_url(file_obj["url"]),
                    "size": file_obj["size"], "type": file_obj["type"], "index": str(i)}  # index为文件的接口列表自然序号，仅供前端使用
        ret_file_list.append(ret_file)
    return {"c": SUCCESS[0], "m": SUCCESS[1], "d": ret_file_list}


def delete_file(user, activity_id, file_id_list):
    activity_id = int(activity_id)
    file_id_list = json.loads(file_id_list)
    file_id_list = map(lambda x: int(x), file_id_list)
    assigned_file_id_list = Work.objects.filter(uploader=user, rar_file__isnull=False, del_flag=FALSE_INT).values_list("rar_file_id", flat=True)
    FileObj.objects.filter(uploader_id=user.id, type=FILE_TYPE_ZIP[0], activity_id=activity_id, id__in=file_id_list, del_flag=FALSE_INT)\
        .exclude(id__in=assigned_file_id_list).update(del_flag=TRUE_INT)
    return {"c": SUCCESS[0], "m": SUCCESS[1], "d": []}


def add_file(user, file_name, file_url, type_list=SUPPORTED_FILE_TYPE, absolute_url=None):
    user_id = 0
    if user:
        user_id = user.id
    file_size = get_object_storage_obj().size(file_url)

    # 获取文件类型，若type_list为空，支持上传所有文件类型
    file_type, ext = get_file_type(file_name, SUPPORTED_FILE_TYPE)
    if not file_type:
        if not type_list:  # 支持上传所有文件类型
            file_type = FILE_TYPE_UNKNOWN[0]
        else:
            return {"c": ERR_FILE_FORMAT_NOT_SUPPORTED[0], "m": ERR_FILE_FORMAT_NOT_SUPPORTED[1], "d": []}

    # 检查文件是否存在
    if not get_object_storage_obj().exists(file_url):
        raise Exception(u"文件不存在")

    # 保存文件信息
    file_obj, created = FileObj.objects.get_or_create(name=file_name, url=file_url, size=file_size, type=file_type,
                                      ext=ext, uploader_id=user_id)
    # 返回文件信息
    abs_url = get_file_url(file_url, absolute_url)
    ret_dict = {"id": file_obj.id, 'url': abs_url, 'type': file_type, 'size': file_size, "name": file_name}
    dict_resp = {"c": SUCCESS[0], "m": SUCCESS[1], "d": [ret_dict]}
    return dict_resp
