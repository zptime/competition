# coding=utf-8
import datetime
import logging

from django.db import transaction

from applications.upload_resumable.err_code import *
from applications.upload_resumable.models import *
from applications.upload_resumable.utils_data import *

logger = logging.getLogger(__name__)

# 针对每个文件的操作创建一个数据库锁
# initiate_multipart_upload part_num=0
# complete_upload part_num=99999999

@transaction.atomic
def upload_lock_acquire(name, part_num):
    created_file_part = None
    ret_code = UPLOAD_ACQUIRE_NOT_IDLE

    # 检查锁占用时间是否超时 , create_time__gt=due_time
    now = datetime.datetime.now()
    file_part = FilePart.objects.filter(name=name, part_num=part_num).first()
    running_due_time = now - datetime.timedelta(seconds=UPLOAD_LOCK_RUNNING_TIMEOUT_SECONDS)
    finish_due_time = now - datetime.timedelta(days=UPLOAD_LOCK_FINISH_TIMEOUT_DAYS)
    if not file_part:
        pass
    elif file_part.status == UPLOAD_STATUS_RUNNING:
        if file_part.update_time > running_due_time:
            logger.info("upload_lock: file_name=%s, part_num=%d have running locked " % (name, part_num))
            return False, UPLOAD_ACQUIRE_RUNNING
        else:
            FilePart.objects.filter(name=name, part_num=part_num).delete()
            logger.info("upload_lock: file_name=%s, part_num=%d is running timeout " % (name, part_num))
            ret_code = UPLOAD_ACQUIRE_RUNNING_TIME_OUT
    elif file_part.status == UPLOAD_STATUS_FINISHED:
        if file_part.update_time > finish_due_time:
            logger.info("upload_lock: file_name=%s, part_num=%d have finish locked " % (name, part_num))
            return False, UPLOAD_ACQUIRE_FINISH
        else:
            FilePart.objects.filter(name=name).delete()
            logger.info("upload_lock: file_name=%s, part_num=%d is finish timeout " % (name, part_num))
            ret_code = UPLOAD_ACQUIRE_FINISH_TIME_OUT

    # 创建正在上传的文件块
    try:
        created_file_part = FilePart.objects.create(name=name, part_num=part_num)
    except Exception as ex:
        pass
    if created_file_part:
        logger.info("upload_lock: file_name=%s, part_num=%d acquire success " % (name, part_num))
        return True, ret_code
    else:
        logger.info("upload_lock: file_name=%s, part_num=%d doesn't get lock " % (name, part_num))
        return False, ret_code


# 文件上传完成后，释放锁
@transaction.atomic
def upload_lock_release(name, part_num):
    FilePart.objects.filter(name=name, part_num=part_num).delete()
    logger.info("upload_lock: file_name=%s, part_num=%d release lock " % (name, part_num))

# 文件上传出错后，释放所有锁
@transaction.atomic
def upload_lock_release(name):
    FilePart.objects.filter(name=name).delete()
    logger.info("upload_lock: file_name=%s release lock " % (name))

@transaction.atomic
def upload_lock_finish(name, part_num):
    FilePart.objects.filter(name=name, part_num=part_num).update(status=UPLOAD_STATUS_FINISHED, update_time=datetime.datetime.now())
    logger.info("upload_lock: file_name=%s, part_num=%d finish lock " % (name, part_num))


@transaction.atomic
def upload_complete(user, file_name, src_file_name, file_size, md5sum="", activity_id=0, cur_user_id=0):
    file_type, ext = get_file_type(file_name)
    url = file_name
    file_obj = FileObj.objects.filter(url=url).first()

    if not file_obj:
        file_obj = FileObj.objects.create(name=src_file_name, url=url, size=file_size, type=file_type,
                                          ext=ext, uploader_id=user.id, activity_id=activity_id, md5sum=md5sum)
    elif file_obj.del_flag == 1:
        file_obj.del_flag = 0
        file_obj.name = src_file_name
        file_obj.size = file_size
        file_obj.type = file_type
        file_obj.ext = ext
        file_obj.uploader_id = user.id
        file_obj.activity_id = activity_id
        file_obj.md5sum = md5sum
        file_obj.save()
    abs_url = get_file_url(url)
    ret_dict = {"id": file_obj.id, 'url': abs_url, 'type': file_type, 'size': file_size, "name": src_file_name}
    dict_resp = {"c": UPLOAD_ERR_FILE_SUCCESS[0], "m": UPLOAD_ERR_FILE_SUCCESS[1], "d": [ret_dict]}
    return dict_resp



