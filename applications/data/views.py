# coding=utf-8
import base64
import cStringIO
import os
import datetime
from PIL import Image
import logging
import json
import traceback
import ueditor_settings
from django.http import HttpResponse
from applications.common.services import get_curuser_by_id
from applications.upload_resumable.storage.object_storage import get_operator
from competition_v3.settings.base import UPLOAD_IMAGE_EXTENSION, ARTICLE_IMAGE_TEMP, UPLOAD_IMAGE_SIZE, UPLOAD_VIDEO_EXTENSION, ARTICLE_VIDEO_TEMP, \
    UPLOAD_VIDEO_SIZE, UPLOAD_FILE_EXTENSION, ARTICLE_FILE_TEMP, UPLOAD_FILE_SIZE, BASE_DIR
from utils.check_param import getp, InvalidHttpParaException
from utils.net_helper import response_parameter_error, response_exception, response200
from utils.public_fun import get_relative_path, gen_rnd_filename, suuid
import agents
from utils.check_auth import validate
from utils.const_def import *
from utils.const_err import *
from utils.utils_except import BusinessException
from utils.utils_log import log_response, log_request

logger = logging.getLogger(__name__)


@validate('POST', auth=False)
def api_upload_file(request):
    try:
        file_obj = request.FILES['file']
        activity_id = request.POST.get("activity_id", 0)
        cur_user_id = getp(request.POST.get('cur_user_id'), nullable=True, para_intro='当前用户ID')

        dictResp = agents.upload_file(user=request.user, file_obj=file_obj, activity_id=activity_id, cur_user_id=cur_user_id)
        log_response(request, dictResp)
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")

    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dictResp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")


@validate('POST', auth=False)
def api_list_file(request):
    try:
        activity_id = request.POST.get("activity_id", "")
        file_name = request.POST.get("file_name", "")
        work_id = request.POST.get("work_id", "")
        cur_user_id = getp(request.POST.get('cur_user_id'), nullable=True, para_intro='当前用户ID')

        cur_user = get_curuser_by_id(cur_user_id)
        dictResp = agents.list_file(request.user, cur_user, activity_id, file_name, work_id)
        log_response(request, dictResp)
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")

    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dictResp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")


@validate('POST', auth=True)
def api_delete_file(request):
    try:
        file_id_list = request.POST.get("file_id_list", "")
        activity_id = request.POST.get("activity_id", "")
        cur_user_id = getp(request.POST.get('cur_user_id'), nullable=True, para_intro='当前用户ID')

        cur_user = get_curuser_by_id(cur_user_id)
        dictResp = agents.delete_file(cur_user, activity_id, file_id_list)
        log_response(request, dictResp)
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")

    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dictResp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")

UPLOAD_FIELD_NAME = {
    "uploadfile": "fileFieldName",
    "uploadimage": "imageFieldName",
    # "uploadscrawl":"scrawlFieldName", # 暂不不支持上传涂鸦
    "catchimage": "catcherFieldName",
    "uploadvideo": "videoFieldName",
}


def api_ueditor_controller(request):
    action = request.GET.get("action", "")
    response_action = {
        "config": get_ueditor_settings,
        "uploadimage": ueditor_upload_file,
        # "uploadscrawl": UploadFile, # 暂不支持
        "uploadvideo": ueditor_upload_file,
        "uploadfile": ueditor_upload_file,
        # "catchimage": catcher_remote_image, # 暂不支持
        # "listimage": list_files,
        # "listfile": list_files
    }
    if action not in response_action.keys():
        dictResp = {'c': ERR_ACTION_NOT_SUPPORT[0], 'm': ERR_ACTION_NOT_SUPPORT[1]}
        return HttpResponse(json.dumps(u"{'state:'ERROR'}"), content_type="application/javascript")
    else:
        return response_action[action](request)


def get_ueditor_settings(request):
    try:
        return HttpResponse(json.dumps(ueditor_settings.UEditorUploadSettings, ensure_ascii=False), content_type="application/javascript")
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dictResp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")


@validate('POST', auth=True)
def ueditor_upload_file(request):
    try:
        action = request.GET.get("action", "")
        upload_field_name = request.GET.get(UPLOAD_FIELD_NAME.get(action, ""), "upfile")
        file_obj = request.FILES.get(upload_field_name, None)
        if file_obj is None:
            return HttpResponse(json.dumps(u"{'state:'ERROR'}"), content_type="application/javascript")

        dictResp = agents.ueditor_controller(request.user, file_obj)
        log_response(request, dictResp)
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")

    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        dictResp = {"c": -1, "m": ex.message}
        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")


# def list_files(request):
#     """列出文件"""
#     #取得动作
#     action = request.GET.get("action", "listimage")
#
#     allowFiles={
#         "listfile": settings.UEditorUploadSettings.get("fileManagerAllowFiles",[]),
#         "listimage": settings.UEditorUploadSettings.get("imageManagerAllowFiles",[])
#     }
#     listSize={
#         "listfile": settings.UEditorUploadSettings.get("fileManagerListSize", ""),
#         "listimage": settings.UEditorUploadSettings.get("imageManagerListSize", "")
#     }
#     listpath={
#         "listfile": settings.UEditorUploadSettings.get("fileManagerListPath", ""),
#         "listimage": settings.UEditorUploadSettings.get("imageManagerListPath", "")
#     }
#     #取得参数
#     list_size = long(request.GET.get("size", listSize[action]))
#     list_start = long(request.GET.get("start", 0))
#
#     files = []
#     root_path = os.path.join(settings.gSettings.MEDIA_ROOT,listpath[action]).replace("\\", "/")
#     files = get_files(root_path, root_path, allowFiles[action])
#
#     if len(files) == 0:
#         return_info={
#             "state":u"未找到匹配文件！",
#             "list":[],
#             "start":list_start,
#             "total":0
#         }
#     else:
#         return_info={
#             "state":"SUCCESS",
#             "list":files[list_start:list_start+list_size],
#             "start":list_start,
#             "total":len(files)
#         }
#
#     return HttpResponse(json.dumps(return_info), content_type="application/javascript")
#
#
# def get_files(root_path, cur_path, allow_types=[]):
#     files = []
#     items = os.listdir(cur_path)
#     for item in items:
#         item=unicode(item)
#         item_fullname = os.path.join(root_path,cur_path, item).replace("\\", "/")
#         if os.path.isdir(item_fullname):
#             files.extend(get_files(root_path,item_fullname, allow_types))
#         else:
#             ext = os.path.splitext(item_fullname)[1]
#             is_allow_list= (len(allow_types)==0) or (ext in allow_types)
#             if is_allow_list:
#                 files.append({
#                     "url":urllib.basejoin(USettings.gSettings.MEDIA_URL ,os.path.join(os.path.relpath(cur_path,root_path),item).replace("\\","/" )),
#                     "mtime":os.path.getmtime(item_fullname)
#                 })
#
#     return files


@validate("POST", auth=True)
def ckupload(request):
    """CKEditor 文件上传
    不要修改返回错误中的英文描述，否则报错时，页面会无法明确报错"""
    error = ''
    url = ''
    callback = request.GET.get("CKEditorFuncNum", '')
    try:
        if request.method == 'POST' and 'upload' in request.FILES:
            fileobj = request.FILES.get('upload', None)  # request.FILES['upload']
            fname, fext = os.path.splitext(fileobj.name)
            rnd_name = '%s%s' % (gen_rnd_filename(fname), fext)

            logger.info(fileobj.size)
            # 根据扩展名，将文件放到不同的目录
            if fext in UPLOAD_IMAGE_EXTENSION:
                server_upload_dir = ARTICLE_IMAGE_TEMP
                file_max_size = UPLOAD_IMAGE_SIZE
            elif fext in UPLOAD_VIDEO_EXTENSION:
                server_upload_dir = ARTICLE_VIDEO_TEMP
                file_max_size = UPLOAD_VIDEO_SIZE
            elif fext in UPLOAD_FILE_EXTENSION:
                server_upload_dir = ARTICLE_FILE_TEMP
                file_max_size = UPLOAD_FILE_SIZE
            else:
                raise BusinessException(FILE_UPLOAD_FORBID)

            if fileobj.size > file_max_size:
                raise BusinessException(FILE_UPLOAD_TOOBIG)

            if not settings.USE_S3:
                filepath = os.path.join(BASE_DIR, 'media', server_upload_dir % datetime.datetime.now().strftime('%Y%m'), rnd_name)
                # 检查路径是否存在，不存在则创建
                dirname = os.path.dirname(filepath)
                if not os.path.exists(dirname):
                    try:
                        os.makedirs(dirname)
                    except:
                        raise BusinessException(ERROR_CREATE_DIR)
                elif not os.access(dirname, os.W_OK):
                    raise BusinessException(ERROR_DIR_NOT_WRITEABLE)

            # 写入文件
            if not error:
                if settings.USE_S3:
                    dict_resp = agents.upload_file(request.user, fileobj)
                    if dict_resp["c"] != SUCCESS[0]:
                        logger.error(dict_resp)
                        uploaded = '0'
                        error = 'post error'
                        # error = ERR_DATA_WRITE_ERR[1]
                    else:
                        uploaded = '1'
                        file_info = dict_resp["d"][0]
                        url = file_info["url"]
                        original = file_info["name"]
                        type = file_info["type"]
                        size = file_info["size"]
                else:
                    # fileobj.save(filepath)
                    destination = open(filepath, 'wb+')  # 打开特定的文件进行二进制的写操作
                    for chunk in fileobj.chunks():  # 分块写入文件
                        destination.write(chunk)
                    destination.close()

                    # url = url_for('static', filename='%s/%s' % ('upload', rnd_name))
                    url = '/media/%s%s' % (server_upload_dir % datetime.datetime.now().strftime('%Y%m'), rnd_name)
                    uploaded = '1'
        else:
            error = 'post error'
            uploaded = '0'
    except BusinessException as e:
        error = 'post error'
        uploaded = '0'
        logger.exception(e.msg)
    except Exception as ipe:
        logger.exception(ipe)
        error = 'post error'
        uploaded = '0'

    # 根据情况返回不同的内容
    if callback:
        res = """

    <script type="text/javascript">
     window.parent.CKEDITOR.tools.callFunction(%s, '%s', '%s');
    </script>

    """ % (callback, url, error)
    else:
        if uploaded == "0":
            res = """
            {"error":{"number":105,"message":"%s"}}
            """ % error
            # return HttpResponse(res, status=400)

        else:
            res = """
            {"fileName":"%s","uploaded":"%s","url":"%s"}
            """ % (fileobj.name, uploaded, url)

    # response = make_response(res)
    # response.headers["Content-Type"] = "text/html"
    # return response
    return HttpResponse(res)



def save_as_base64(image):
    image_buffer = cStringIO.StringIO()
    image = image.convert('RGB')
    image.save(image_buffer, format="JPEG")
    return base64.b64encode(image_buffer.getvalue())   # 不包含 data:image/jpeg;base64,


def image_process(img_path, w_want, h_want):
    file_path = os.path.join(settings.BASE_DIR, img_path)
    get_operator().download_file(get_relative_path(file_path), file_path)
    pil = Image.open(file_path)
    width, height = pil.size
    try:
        x = int(w_want) or width
        y = int(h_want) or height
    except Exception as e:
        x = width
        y = height
    if width > x or height > y:
        # PIL会等比缩放到长与宽都小于指定值
        pil.thumbnail((x, y), Image.ANTIALIAS)
    b64 = save_as_base64(pil)
    return pil, b64


def image_base64(img_path, width, height):
    _, b64 = image_process(img_path, width, height)
    return response200({'c': SUCCESS[0], 'm': SUCCESS[1], 'd': b64})


def image_stream(img_path, width, height):
    response = HttpResponse(content_type=IMAGE_FORMAT[IMAGE_FORMAT_DEFAULT][0])
    pil, _ = image_process(img_path, width, height)
    pil.save(response, IMAGE_FORMAT[IMAGE_FORMAT_DEFAULT][1])
    response['Content-Encoding'] = 'utf-8'
    response['Content-Disposition'] = 'attachment;filename=%s_w%s_h%s.%s' % (suuid(), width, height, IMAGE_FORMAT_DEFAULT)
    return response


@validate('GET', auth=False)
def api_image(request, img):
    # logger.info(request)
    width = request.GET.get('w', '0')
    height = request.GET.get('h', '0')
    result_type = request.GET.get('t', IMAGE_CONTENT_TYPE_DEFAULT)

    if result_type == IMAGE_CONTENT_TYPE_BASE64:
        return image_base64(img, width, height)
    else:
        return image_stream(img, width, height)
