#!/usr/bin/env python
# coding=utf-8

from django.core.files import File
from django.db.models import Q
from django.db import transaction
from django.conf import settings
import datetime
import logging
import traceback
import os
import platform

from models import *
from utils.const_err import SUCCESS
from utils.file_fun import get_image_url
from utils.public_fun import download_file
from applications.data.agents import upload_file
from task import resize_image, get_swf_img

from converter import Converter

logger = logging.getLogger(__name__)


class VideoConverterTask(object):
    task_name = "video converting task"
    option = {
        'format': 'mp4',
        'audio': {
            'codec': 'aac',
            # 'samplerate': 11025,
            # 'channels': 2
        },
        'video': {
            'codec': 'h264',
            'width': 720,
            'height': 480,
            # 'fps': 15
        },
        'subtitle': {
            'codec': 'copy'
        },
        'map': 0
    }

    def __init__(self):
        self.obj = None
        self.local_file_path = None
        self.converted_file_path = None
        self.task_status = None
        self.converter = None
        self.thumbnail_path = None

    @transaction.atomic
    def __get_video_unprocessed(self):
        self.obj = WorkFileObj.objects.filter(del_flag=FALSE_INT, task_status=TASK_STATUS_NOT_PROCESS[0]).\
            filter(Q(src_file__type=FILE_TYPE_MP4[0]) | Q(src_file__type=FILE_TYPE_FLV[0]) | Q(src_file__type=FILE_TYPE_SWF[0])).first()
        now = datetime.datetime.now()
        if self.obj:
            self.task_status = TASK_STATUS_PROCESSING[0]
            self.obj.task_status = self.task_status
            self.obj.task_time = now
            self.obj.save()
        else:
            pass

    def __download_video(self):
        video_file = FileObj.objects.filter(del_flag=FALSE_INT, id=self.obj.src_file.id).first()
        if not video_file:
            raise Exception(u"找不到相应的文件!")
        video_file_url = get_image_url(video_file.url, abs=True)
        self.local_file_path = download_file(video_file_url)

    def __check_video_convert_needed(self):
        video_type = self.obj.src_file.type
        if video_type == FILE_TYPE_FLV[0] or video_type == FILE_TYPE_SWF[0]:
            return False
        else:
            info = self.converter.probe(self.local_file_path)
            encode = info.video.codec
            if encode == "h264":  # MP4格式也需要转码调整码流
                if self.obj.src_file.ext.lower() == FILE_TYPE_MP4[1][0]:
                    return True
                else:
                    return True
            else:
                return True

    @staticmethod
    def __init_converter():
        """
            在Windows系统中使用的文件名在Linux系统中忽略：
        """
        path_ffmpeg = None
        path_ffprobe = None
        if 'windows' in platform.system().lower():
            path_ffmpeg = "ffmpeg.exe"
            path_ffprobe = "ffprobe.exe"
        elif "linux" in platform.system().lower():
            pass
        else:
            pass
        return Converter(path_ffmpeg, path_ffprobe)

    def __video_convert_thumbnail(self):
        try:
            self.converter = self.__init_converter()
        except Exception:
            raise
        logger.debug(u"【开始】抽取视频图片，视频文件路径：%s " % self.local_file_path)
        self.thumbnail_path = self.local_file_path.split(".")[0] + ".png"
        if os.path.exists(self.thumbnail_path):
            os.remove(self.thumbnail_path)
        if self.obj.src_file.type != FILE_TYPE_SWF[0]:
            self.converter.thumbnail(self.local_file_path, 5, self.thumbnail_path)
        else:
            # cmd = "/usr/bin/swfrender -p 1 " + self.local_file_path + " -o " + self.thumbnail_path
            # os.system(cmd)
            get_swf_img(self.local_file_path, self.thumbnail_path)

        if os.path.exists(self.thumbnail_path):
            logger.debug(u"【成功】抽取视频图片，图片文件路径：%s " % self.thumbnail_path)
        else:
            logger.debug(u"【失败】抽取视频图片，图片文件路径：%s 不存在" % self.thumbnail_path)
        resize_img_path = resize_image(self.thumbnail_path)
        if resize_img_path:
            os.remove(self.thumbnail_path)
            self.thumbnail_path = resize_img_path

        if self.__check_video_convert_needed():
            try:
                logger.debug(u"【开始】转码视频格式，源视频文件路径：%s " % self.local_file_path)
                self.converted_file_path = self.local_file_path.split(".")[0] + "_1.mp4"
                if os.path.exists(self.converted_file_path):
                    os.remove(self.converted_file_path)
                conv = self.converter.convert(self.local_file_path, self.converted_file_path, self.option)
                for _ in conv:
                    pass
                if os.path.exists(self.converted_file_path):
                    self.obj.task_output = u"视频转码成功。"
                    logger.debug(u"【成功】转码视频格式，转码后视频文件路径：%s " % self.converted_file_path)
                else:
                    raise Exception("not found converted_file_path")
            except Exception, e:
                self.task_status = TASK_STATUS_PROCESSED_ERROR[0]
                self.obj.task_status = self.task_status
                self.obj.task_output = u"视频转码失败:" + e.message
                logger.debug(u"【失败】转码视频格式，没有找到转码后视频文件：%s " % self.converted_file_path)
                raise e
        else:
            self.obj.task_output = u"支持的视频格式,不需要转换。"
            logger.debug(u"视频文件不需要转码：源视频文件路径%s" % self.local_file_path)

    def __upload_file(self):
        if self.task_status == TASK_STATUS_PROCESSING[0]:
            if self.thumbnail_path:
                logger.debug(u"准备上传图片%s" % self.thumbnail_path)
                file_obj = open(self.thumbnail_path, 'rb')
                file_obj = File(file_obj, os.path.basename(self.thumbnail_path))
                resp_dict = upload_file(user=None, file_obj=file_obj, activity_id=self.obj.work.activity_id, prefix=self.obj.work.no)
                if resp_dict["c"] != SUCCESS[0]:
                    raise Exception(u"[%s]文件上传出错--%s" % (self.thumbnail_path, resp_dict["m"]))
                file_info_list = resp_dict["d"]
                if not file_info_list:
                    if os.path.exists(self.thumbnail_path):
                        os.remove(self.thumbnail_path)
                    raise Exception(u"[%s]文件上传返回值为空" % self.thumbnail_path)
                self.obj.img_file_id = file_info_list[0]["id"]
            else:
                if self.obj.src_file.type == FILE_TYPE_SWF[0]:
                    self.obj.img_file_id = self.obj.src_file.id
            if self.converted_file_path:
                logger.debug(u"准备上传转码后文件%s" % self.converted_file_path)
                file_obj = open(self.converted_file_path, 'rb')
                file_obj = File(file_obj, os.path.basename(self.converted_file_path))
                resp_dict = upload_file(user=None, file_obj=file_obj, activity_id=self.obj.work.activity_id, prefix=self.obj.work.no)
                if resp_dict["c"] != SUCCESS[0]:
                    raise Exception(u"[%s]文件上传出错--%s" % (self.converted_file_path, resp_dict["m"]))
                file_info_list = resp_dict["d"]
                if not file_info_list:
                    if os.path.exists(self.converted_file_path):
                        os.remove(self.converted_file_path)
                    raise Exception(u"[%s]文件上传返回值为空" % self.converted_file_path)
                self.obj.des_file_id = file_info_list[0]["id"]
            else:
                self.obj.des_file_id = self.obj.src_file.id
            self.task_status = TASK_STATUS_PROCESSED_SUCCESS[0]
        else:
            pass

    @transaction.atomic
    def __update_status(self, error_info=None):
        if self.task_status == TASK_STATUS_PROCESSED_SUCCESS[0]:
            self.obj.task_status = self.task_status
            self.obj.task_output += u"视频处理完成"
            self.obj.save()
        else:
            self.obj.task_output += error_info[0:200]
            self.obj.task_status = TASK_STATUS_PROCESSED_ERROR[0]
            self.obj.save()

    def __clean_tmp_file(self):
        if self.local_file_path:
            if os.path.exists(self.local_file_path):
                os.remove(self.local_file_path)
        if self.thumbnail_path:
            if os.path.exists(self.thumbnail_path):
                os.remove(self.thumbnail_path)
        if self.converted_file_path:
            if os.path.exists(self.converted_file_path):
                os.remove(self.converted_file_path)

    def execute(self):
        try:
            # 获取要处理的视频文件
            self.__get_video_unprocessed()
            if not self.obj:
                logger.info("not found an available video to convert")
                return True
            logger.debug("##################work_id[%d],work_file_id[%d],src_file_id[%d]###############################"
                         % (self.obj.work_id, self.obj.id, self.obj.src_file_id))
            logger.debug("Begin process video file id %d " % self.obj.src_file_id)

            # 下载视频文件到本地缓存
            self.__download_video()
            if not self.local_file_path:
                logger.error("[%d]download src video file error" % self.obj.id)
                return False
            logger.debug("Have download rar file %s" % self.local_file_path)

            # 抽取视频文件图片并转码
            self.__video_convert_thumbnail()
            logger.debug("Have convert_thumbnail complete")

            # 上传转码后的文件和图片
            self.__upload_file()
            logger.debug("Have upload all files")

            # 更新状态
            self.__update_status()
            logger.debug("End process video file id %d " % self.obj.src_file_id)
            return False
        except Exception as e:
            err_info = traceback.format_exc()
            logger.error(self.task_name + err_info)
            if self.obj:
                self.__update_status(e.message)
            return False
        finally:
            self.__clean_tmp_file()
            logger.debug("#################################################################")

    @staticmethod
    def execute_loop():
        task_work_num = WorkFileObj.objects.filter(task_status=TASK_STATUS_PROCESSING[0], del_flag=FALSE_INT).\
            filter(Q(src_file__type=FILE_TYPE_MP4[0]) | Q(src_file__type=FILE_TYPE_FLV[0]) | Q(src_file__type=FILE_TYPE_SWF[0])).count()
        if task_work_num > settings.VIDEO_CONVERT_TASK_WORK_NUM:
            logger.info("There are %d tasks executing" % task_work_num)
            return

        while True:
            task_obj = VideoConverterTask()
            if task_obj.execute():
                logger.info("have process all")
                break


