# coding=utf-8
from models import *
from utils.const_err import SUCCESS
from utils.file_fun import *
from utils.public_fun import *
from django.db.models import F
from PIL import Image
from applications.data.agents import upload_file
from django.core.files import File

logger = logging.getLogger(__name__)


def task_unzip_task():
    return


def task_change_video_format():
    return


def task_change_doc_format():
    return


def resize_image_and_upload(src_file_path, activity_id, work_no):
    if not src_file_path or not activity_id or not work_no:
        logger.error("resize_image have null parameter ")
        return None
    dst_file_path = resize_image(src_file_path)
    if not dst_file_path:
        return None
    logger.debug("[begin] upload resize image file %s " % dst_file_path)
    with open(dst_file_path, 'rb') as file_obj:
        file_obj = File(file_obj, os.path.basename(dst_file_path))
        resp_dict = upload_file(user=None, file_obj=file_obj, type_list=[],
                                activity_id=activity_id, prefix=work_no)
    if resp_dict["c"] != SUCCESS[0]:
        logger.error("[error1] upload resize image file %s " % dst_file_path)
    file_info_list = resp_dict["d"]
    if not file_info_list:
        logger.error("[error2] upload resize image file %s " % dst_file_path)
    return file_info_list[0]["id"]


def resize_image(src_file_path):
    logger.debug("resize image file %s " % src_file_path)
    dst_file_path = get_new_file_name_with_suffix(src_file_path, "550_400", ".jpg")
    clip_resize_img(ori_img=src_file_path, dst_img=dst_file_path, dst_w=550, dst_h=400, save_q=75)
    if not os.path.exists(dst_file_path):
        logger.error("resize image file error %s" % src_file_path)
        return ""
    return dst_file_path


def clip_resize_img(**args):
    args_key = {'ori_img': '', 'dst_img': '', 'dst_w': '', 'dst_h': '', 'save_q': 75}
    arg = {}
    for key in args_key:
        if key in args:
            arg[key] = args[key]

    img = Image.open(arg['ori_img'])
    ori_w, ori_h = img.size

    dst_scale = float(arg['dst_h']) / arg['dst_w']  # 目标高宽比
    ori_scale = float(ori_h) / ori_w  # 原高宽比

    if ori_scale >= dst_scale:
        # 过高
        width = ori_w
        height = int(width * dst_scale)

        x = 0
        y = (ori_h - height) / 2

    else:
        # 过宽
        height = ori_h
        width = int(height / dst_scale)

        x = (ori_w - width) / 2
        y = 0

    # 裁剪
    box = (x, y, width + x, height + y)
    # 这里的参数可以这么认为：从某图的(x,y)坐标开始截，截到(width+x,height+y)坐标, 所包围的图像
    newIm = img.crop(box)
    img = None

    # 压缩
    ratio = float(arg['dst_w']) / width
    newWidth = int(width * ratio)
    newHeight = int(height * ratio)
    newIm.convert('RGB').resize((newWidth, newHeight), Image.ANTIALIAS).save(arg['dst_img'], quality=arg['save_q'])


def old_resize_image(src_file_path):
    logger.debug("resize image file %s " % src_file_path)
    dst_file_path = get_new_file_name_with_suffix(src_file_path, "550_400", ".jpg")
    img = Image.open(src_file_path)
    new_img = img.resize((550, 400), Image.BILINEAR)
    new_img.convert('RGB').save(dst_file_path)
    if not os.path.exists(dst_file_path):
        logger.error("resize image file error %s" % src_file_path)
        return ""
    return dst_file_path


# 将作品文件重命名为作品编号
def rename_work_rar_file():
    logger.debug("###########################Rename work rar file name#################################")
    work_list = Work.objects.filter(rar_file__isnull=False, del_flag=FLAG_NO, rar_file__size__lte=2000000000).exclude(rar_file__url__contains=F("no"))
    for work_obj in work_list:
        rar_file_obj = work_obj.rar_file
        if not rar_file_obj:
            logger.error(u"[%d]没有找到对应的作品压缩文件" % work_obj.id)
        src_obj_path = rar_file_obj.url
        ext = os.path.splitext(src_obj_path)[-1]
        dir_name = os.path.dirname(src_obj_path)
        dst_obj_path = os.path.join(dir_name, work_obj.no + ext)
        ret = get_object_storage_obj().copy(src_obj_path, dst_obj_path)
        if not ret:
            logger.error("rename rar file error")
        else:
            if Work.objects.filter(rar_file__url=src_obj_path).exclude(id=work_obj.id).exists():
                file_obj = FileObj.objects.create(name=rar_file_obj.name, url=dst_obj_path, size=rar_file_obj.size,
                                                  type=rar_file_obj.type, ext=rar_file_obj.ext,
                                                  modify_time=rar_file_obj.modify_time, status=rar_file_obj.status,
                                                  uploader_id=rar_file_obj.uploader_id, activity_id=rar_file_obj.activity_id,
                                                  )
                work_obj.rar_file = file_obj
                work_obj.save()
                logger.info("more than one work with same work_obj %s" % src_obj_path)
            else:
                rar_file_obj.url = dst_obj_path
                rar_file_obj.save()
                get_object_storage_obj().delete(src_obj_path)


def task_refresh_preview_status():
    work_obj_list = Work.objects.filter(task_status=TASK_STATUS_PROCESSED_SUCCESS[0], preview_status=WORK_PREVIEW_STATUS_NONE[0], del_flag=FLAG_NO)
    for work_obj in work_obj_list:
        if WorkFileObj.objects.filter(work=work_obj, task_status__in=[TASK_STATUS_NOT_PROCESS[0], TASK_STATUS_PROCESSING[0]],
                                      del_flag=FALSE_INT).exists():
            continue
        work_file_obj = WorkFileObj.objects.filter(work=work_obj, del_flag=FALSE_INT, permission=FILE_PERMISSION_ALL[0]). \
            exclude(des_file__isnull=True, img_file__isnull=True).first()
        if work_file_obj:
            work_obj.preview_status = WORK_PREVIEW_STATUS_SUPPORTED[0]
            work_obj.img_file = work_file_obj.img_file
            work_obj.save()


def clean_task_files():
    work_list = Work.objects.all()
    for work_obj in work_list:
        work_file_obj_list = WorkFileObj.objects.filter(work=work_obj)
        work_obj.img_file_id = None
        work_obj.task_status = TASK_STATUS_NOT_PROCESS[0]
        work_obj.task_time = None
        work_obj.task_output = ""
        work_obj.preview_status = WORK_PREVIEW_STATUS_NONE[0]
        work_obj.save()
        for work_file_obj in work_file_obj_list:
            if work_file_obj.img_file:
                remove_obj_storage_file(work_file_obj.img_file.url)
            if work_file_obj.des_file:
                remove_obj_storage_file(work_file_obj.des_file.url)
            if work_file_obj.src_file:
                remove_obj_storage_file(work_file_obj.src_file.url)
            work_file_obj.delete()
            FileObj.objects.filter(id=work_file_obj.img_file_id).delete()
            FileObj.objects.filter(id=work_file_obj.des_file_id).delete()
            FileObj.objects.filter(id=work_file_obj.src_file_id).delete()


import commands
import os


def get_swf_img(swf_file, output_file):
    cmd_str = "swfextract %s | grep JPEGs" % swf_file
    (status, output) = commands.getstatusoutput(cmd_str)
    if status != 0:
        print "error" + output
    id_list = output.split()
    if len(id_list) < 4:
        print "swf not have jpeg img"
    id_list = id_list[4:]
    for id in id_list:
        cmd_str = "swfextract %s -j %d -o %s" % (swf_file, id, output_file)
        (status, output) = commands.getstatusoutput(cmd_str)
        if status != 0:
            print id
            continue
        elif os.path.exists(output_file) and os.stat(output_file).st_size < 2 * 1024:
            continue
        else:
            return output_file

    # try swfrender
    cmd_str = "swfrender -p 5 %s -o %s" % (swf_file, output_file)
    (status, output) = commands.getstatusoutput(cmd_str)


import os
import commands

max_render_page = 2000
render_page_step = 10
min_file_size = 1024 * 5


def get_swf_img(swf_file, output_file):
    cmd_str = "swfextract %s | grep JPEG" % swf_file
    logger.debug(cmd_str)
    (status, output) = commands.getstatusoutput(cmd_str)
    if status != 0:
        logger.error("error: " + str(status))
    id_list = output.split()
    if len(id_list) < 4:
        logger.debug("swf not include jpeg img")
    id_list = id_list[4:]
    for no in id_list:
        cmd_str = "swfextract %s -j %s -o %s" % (swf_file, no, output_file)
        logger.debug(cmd_str)
        (status, output) = commands.getstatusoutput(cmd_str)
        if status != 0:
            logger.debug("swfextract ret_status=%s", str(status))
            continue
        elif not os.path.exists(output_file) or os.stat(output_file).st_size < min_file_size:
            continue
        else:
            logger.debug("success from swfextract")
            return output_file

    # try swfrender
    max_size = 0
    max_size_page = 0
    i = 0
    while i < max_render_page:
        i += render_page_step
        cmd_str = "swfrender -p %d %s -o %s" % (i, swf_file, output_file)
        logger.debug(cmd_str)
        (status, output) = commands.getstatusoutput(cmd_str)
        if status != 0 or os.path.exists(output_file):
            break
        elif os.stat(output_file).st_size < min_file_size:
            file_size = os.stat(output_file).st_size
            if file_size > max_size:
                max_size = file_size
                max_size_page = i
                os.remove(output_file)
            logger.debug("swfrender p=%d  size=%d" % (i, file_size))
            continue
        else:
            logger.debug("success from swfrender")
            return output_file
    if i >= max_render_page:
        cmd_str = "swfrender -p %d %s -o %s" % (max_size_page, swf_file, output_file)
        logger.debug(cmd_str)
        (status, output) = commands.getstatusoutput(cmd_str)
