# -*- coding: utf-8 -*-
import json
import traceback
import logging

from django.http import HttpResponse
from django.views.generic import View
from django.conf import settings

from applications.upload_resumable.err_code import *
from applications.upload_resumable.utils_data import gen_err_code_response
from applications.upload_resumable.utils_upload import *

if settings.DATA_STORAGE_USE_S3:
    from files_s3 import ResumableFile
else:
    from files import ResumableFile

logger = logging.getLogger(__name__)


class ResumableUploadView(View):
    def get(self, *args, **kwargs):
        """Checks if chunk has allready been sended.
        """
        try:
            r = ResumableFile(self.request.GET, self.request.user)
            logger.debug("[GET] Resumable Upload file_name %s part_num %d" % (r.filename, r.part_num))
            # 检查文件是否已经存在
            if r.is_exist:
                logger.debug("[POST] file have exist")
                dict_resp = upload_complete(self.request.user, r.filename, r.src_filename, r.total_size, r.file_md5sum, int(r.dir_name), r.cur_user_id)
                return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
            # 检查文件块是否已经收集完成
            if r.is_complete:
                err_code = r.process_file()
                if err_code != UPLOAD_ERR_COMPLETE_SUCCESS:
                    return gen_err_code_response(err_code)
                else:
                    logger.debug("[POST] all chunk already exists")
                    dict_resp = upload_complete(self.request.user, r.filename, r.src_filename, r.total_size, r.file_md5sum, int(r.dir_name), r.cur_user_id)
                    return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
            # 检查请求的文件块是否存在
            elif r.chunk_exists:
                logger.debug("[GET] chunk already exists")
                return gen_err_code_response(UPLOAD_ERR_CHUNK_EXIST)
            else:
                logger.debug("[GET] chunk not found")
                return gen_err_code_response(UPLOAD_ERR_CHUNK_NOT_EXIST)
        except Exception as ex:
            sErrInfo = traceback.format_exc()
            logger.error(sErrInfo)
            return gen_err_code_response(UPLOAD_ERR_NOT_KNOWN_ERR)

    def post(self, *args, **kwargs):
        """Saves chunks.
        """
        try:
            chunk = self.request.FILES.get('file')
            r = ResumableFile(self.request.POST, self.request.user)
            logger.debug("[POST] Resumable Upload file_name %s part_num %d" % (r.filename, r.part_num))
            err_code = UPLOAD_ERR_CHUNK_EXIST
            # 检查文件存在，直接返回成功
            if r.is_exist:
                logger.debug("[POST] file have exist")
                dict_resp = upload_complete(self.request.user, r.filename, r.src_filename, r.total_size, r.file_md5sum, int(r.dir_name), r.cur_user_id)
                return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
            # 检查文件块不存在，上传文件块
            if not r.chunk_exists:
                err_code = r.process_chunk(chunk)
                if err_code != UPLOAD_ERR_PART_SUCCESS:
                    return gen_err_code_response(err_code)
            # 检查文件块是否已经收集完成
            if r.is_complete:
                err_code = r.process_file()
                if err_code != UPLOAD_ERR_COMPLETE_SUCCESS:
                    return gen_err_code_response(err_code)
                else:
                    logger.debug("[POST] all chunk already exists")
                    dict_resp = upload_complete(self.request.user, r.filename, r.src_filename, r.total_size, r.file_md5sum, int(r.dir_name), r.cur_user_id)
                    return HttpResponse(json.dumps(dict_resp, ensure_ascii=False), content_type="application/json")
            return gen_err_code_response(err_code)
        except Exception as ex:
            sErrInfo = traceback.format_exc()
            logger.error(sErrInfo)
            return gen_err_code_response(UPLOAD_ERR_NOT_KNOWN_ERR)

