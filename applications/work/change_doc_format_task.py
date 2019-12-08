# coding=utf-8
from models import *
from win32com.client import Dispatch, constants, gencache
from wand.image import Image

from utils.const_err import *
from utils.file_fun import *
from utils.public_fun import *
from applications.data.agents import upload_file
from django.core.files import File
from task import resize_image
import traceback
import time
import os
import re
from django.db import transaction
from wand.color import Color

logger = logging.getLogger(__name__)

# 支持转换的文档类型
support_doc_type = FILE_TYPE_DOC[1] + FILE_TYPE_PPT[1] + FILE_TYPE_XLS[1] + FILE_TYPE_PDF[1]


def GenerateSupport():
    gencache.EnsureModule('{00020905-0000-0000-C000-000000000046}', 0, 8, 4)


def deal_register_form(file_url):
    (filepath, filename) = os.path.split(file_url)
    (name, ext) = os.path.splitext(filename)
    new_txt_file_url = filepath + '/' + name + '.txt'
    if os.path.exists(new_txt_file_url):
        os.remove(new_txt_file_url)
    GenerateSupport()
    word = Dispatch("Word.Application")
    try:
        d = word.Documents.OpenNoRepairDialog(file_url, ReadOnly=1)
        # 将doc文件转换为txt文件处理
        d.SaveAs2(new_txt_file_url, 2)
        with open(new_txt_file_url, 'r') as txt_file:
            line = ""
            # 取txt文件的前3行，拼在一起，用做是否为登记表文件的判断
            for i in range(4):
                line_info = txt_file.readline().decode('gbk')
                line = line + line_info
        is_register_form = None
        introduction_info = None
        # 如果是登记表文件
        if re.search(u'登记表', line) or re.search(u'作品统计表', line):
            is_register_form = 1
            table = d.Tables(1)
            for row in range(1, table.Rows.Count):
                try:
                    row_head_info = table.Cell(Row=row, Column=1).Range.Text
                except:
                    continue
                row_head_info = re.sub(r'[\r\x07\n]', '', row_head_info)
                if re.search(u'作品特点', row_head_info):
                    introduction_info = table.Cell(Row=row, Column=2).Range.Text
                    introduction_info = (re.sub(r'[\r\x07\n]', '', introduction_info)).strip()
                    break
        d.Close(SaveChanges=constants.wdDoNotSaveChanges)
        return {"is_register_form": is_register_form, "introduction_info": introduction_info}
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        raise Exception(u"%s文件在判断登记表处理流程出错" % filename)
    finally:
        if os.path.exists(new_txt_file_url):
            os.remove(new_txt_file_url)
        word.Quit(SaveChanges=constants.wdDoNotSaveChanges)


def doc2pdf(file_url):
    (filepath, filename) = os.path.split(file_url)
    (name, ext) = os.path.splitext(filename)
    new_file_url = filepath + '/' + name + '.pdf'
    if os.path.exists(new_file_url):
        os.remove(new_file_url)
    GenerateSupport()
    word = Dispatch("Word.Application")
    try:
        d = word.Documents.OpenNoRepairDialog(file_url, ReadOnly=1)
        d.SaveAs2(new_file_url, 17)
        d.Close(SaveChanges=constants.wdDoNotSaveChanges)
        return new_file_url
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        raise Exception("%s convert file formats to pdf fails" % filename)
    finally:
        word.Quit(SaveChanges=constants.wdDoNotSaveChanges)


def xls2pdf(file_url):
    (filepath, filename) = os.path.split(file_url)
    (name, ext) = os.path.splitext(filename)
    new_file_url = filepath + '/' + name + '.pdf'
    if os.path.exists(new_file_url):
        os.remove(new_file_url)
    GenerateSupport()
    excel = Dispatch("Excel.Application")
    try:
        e = excel.Workbooks.Open(file_url, ReadOnly=1)
        e.SaveAs(new_file_url, 57)
        e.Close(SaveChanges=False)
        return new_file_url
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        raise Exception("%s convert file formats to pdf fails" % filename)
    finally:
        excel.DisplayAlerts = False
        excel.Quit()


def ppt2pdf(file_url):
    (filepath, filename) = os.path.split(file_url)
    (name, ext) = os.path.splitext(filename)
    new_file_url = filepath + '\\' + name + '.pdf'
    # 这里对url的转换是因为 Powerpoint的SaveAs函数对正斜线的url无法处理
    new_file_url = re.sub('/', '\\\\', new_file_url)
    if os.path.exists(new_file_url):
        os.remove(new_file_url)
    GenerateSupport()
    powerpoint = Dispatch("Powerpoint.Application")
    try:
        p = powerpoint.Presentations.Open(file_url, ReadOnly=1, WithWindow=0)
        p.SaveAs(new_file_url, 32)
        p.Close()
        new_file_url = re.sub('\\\\', '/', new_file_url)
        return new_file_url
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        raise Exception("%s convert file formats to pdf fails" % filename)
    finally:
        powerpoint.Quit()


def pdf2jpg(file_url):
    file_firstpage_url = file_url + '[0]'
    (filepath, filename) = os.path.split(file_url)
    (name, ext) = os.path.splitext(filename)
    img_file_url = filepath + '/' + name + '.jpg'
    try:
        with Image(filename=file_firstpage_url, resolution=200) as img:
            # keep good quality
            img.compression_quality = 100
            img.background_color = Color("white")
            img.alpha_channel = 'remove'
            # save it to new name
            img.save(filename=img_file_url)
        return img_file_url
    except Exception as ex:
        sErrInfo = traceback.format_exc()
        logger.error(sErrInfo)
        raise Exception("%s convert file formats to jpg fails" % filename)


class Change_Doc_Format:
    def __init__(self):
        self.doc_work_obj = None
        self.src_file_obj = None
        self.local_src_file_path = ""
        self.local_des_file_path = ""
        self.local_img_file_path = ""
        self.task_status = ""

    # 获取一个要处理的文档类型的文件
    @transaction.atomic
    def __get_an_available_work(self):
        self.doc_work_obj = WorkFileObj.objects.filter(task_status=TASK_STATUS_NOT_PROCESS[0], src_file__ext__in=support_doc_type,
                                                       del_flag=FALSE_INT).first()
        now = datetime.datetime.now()
        if not self.doc_work_obj:
            out_date = now - datetime.timedelta(minutes=TASK_PROCESSING_TIMEOUT_MINUTES)
            self.doc_work_obj = WorkFileObj.objects.filter(task_status=TASK_STATUS_PROCESSING[0], task_time__lt=out_date,
                                                           src_file__ext__in=support_doc_type, del_flag=FALSE_INT).first()
        if self.doc_work_obj and self.doc_work_obj.src_file:
            self.doc_work_obj.task_time = now
            self.doc_work_obj.task_status = TASK_STATUS_PROCESSING[0]
            self.doc_work_obj.save()

    # 下载文档文件
    def __download_src_file(self):
        self.src_file_obj = FileObj.objects.filter(id=self.doc_work_obj.src_file_id, del_flag=0).first()
        if not self.src_file_obj:
            raise Exception(u"[%d]没有找到作品解压后包含的文档类型的原文件" % self.doc_work_obj.id)

        src_file_url = get_image_url(self.src_file_obj.url, abs=True)
        self.local_src_file_path = download_file(src_file_url)

    # 转换文件格式，获取缩略图
    @transaction.atomic
    def __change_file_format(self):
        if self.src_file_obj.ext in FILE_TYPE_DOC[1]:
            # 对于doc文件是登记表的文件，做特殊处理
            try:
                resp = deal_register_form(self.local_src_file_path)
                if resp["is_register_form"]:
                    # 如果是登记表文件，将文件的权限变为‘游客不能访问’
                    self.doc_work_obj.permission = 15
                    self.doc_work_obj.save()
                    # 如果从登记表文件中提取出了作品特点信息，将其同步到work表中
                    if resp["introduction_info"]:
                        Work.objects.filter(id=self.doc_work_obj.work_id, del_flag=0).update(introduction=resp["introduction_info"])
                logger.debug("[%d]Have judge register_form" % self.doc_work_obj.id)
            except Exception as ex:
                logger.error(ex)

            self.local_des_file_path = doc2pdf(self.local_src_file_path)
            logger.debug("[%d]Have convert doc format to pdf format" % self.doc_work_obj.id)
        elif self.src_file_obj.ext in FILE_TYPE_XLS[1]:
            self.local_des_file_path = xls2pdf(self.local_src_file_path)
            logger.debug("[%d]Have convert xls format to pdf format" % self.doc_work_obj.id)
        elif self.src_file_obj.ext in FILE_TYPE_PPT[1]:
            self.local_des_file_path = ppt2pdf(self.local_src_file_path)
            logger.debug("[%d]Have convert ppt format to pdf format" % self.doc_work_obj.id)
        elif self.src_file_obj.ext in FILE_TYPE_PDF[1]:
            self.local_des_file_path = self.local_src_file_path

        self.local_img_file_path = pdf2jpg(self.local_des_file_path)
        logger.debug("[%d]Have convert pdf format to jpg format" % self.doc_work_obj.id)
        resize_img_path = resize_image(self.local_img_file_path)
        if resize_img_path:
            os.remove(self.local_img_file_path)
            self.local_img_file_path = resize_img_path
        logger.debug("[%d]Have resize img file" % self.doc_work_obj.id)

    # 上传转换后的文件和缩略图文件
    @transaction.atomic
    def __upload_local_files(self):
        # 当原文件就是pdf类型的文件时，不上传
        if not (self.src_file_obj.ext in FILE_TYPE_PDF):
            # 上传转换后的文件
            with open(self.local_des_file_path, 'rb') as des_file_obj:
                des_file_obj = File(des_file_obj, os.path.basename(self.local_des_file_path))
                resp_dict = upload_file(user=None, file_obj=des_file_obj, activity_id=self.doc_work_obj.work.activity_id,
                                        prefix=self.doc_work_obj.work.no)
            if resp_dict["c"] != SUCCESS[0]:
                raise Exception(u"[%d]格式转换后的文档文件上传出错--%s" % (self.doc_work_obj.src_file_id, resp_dict["m"]))
            des_file_info_list = resp_dict["d"]
            if not des_file_info_list:
                raise Exception(u"[%d]文件上传返回值为空" % self.doc_work_obj.id)
            des_file_id = des_file_info_list[0]["id"]
        else:
            des_file_id = self.src_file_obj.id

        # 上传缩略图文件（当上传失败不给异常信息是因为有可能pdf文件上传成功，只是缩略图上传失败, 应该继续执行）
        with open(self.local_img_file_path, 'rb') as img_file_obj:
            img_file_obj = File(img_file_obj, os.path.basename(self.local_img_file_path))
            resp_dict = upload_file(user=None, file_obj=img_file_obj, activity_id=self.doc_work_obj.work.activity_id,
                                    prefix=self.doc_work_obj.work.no)
        if resp_dict["c"] == SUCCESS[0]:
            img_file_info_list = resp_dict["d"]
            if img_file_info_list:
                img_file_id = img_file_info_list[0]["id"]
            else:
                img_file_id = None
        else:
            img_file_id = None

        self.doc_work_obj.des_file_id = des_file_id
        self.doc_work_obj.img_file_id = img_file_id

        self.task_status = TASK_STATUS_PROCESSED_SUCCESS[0]

    # 更新任务状态
    @transaction.atomic
    def __update_task_status(self, err_msg=""):
        if self.task_status == TASK_STATUS_PROCESSED_SUCCESS[0]:
            self.doc_work_obj.task_status = TASK_STATUS_PROCESSED_SUCCESS[0]
            self.doc_work_obj.task_output = u"文件格式转换完成"
            logger.info("[%d]%s" % (self.doc_work_obj.id, self.doc_work_obj.task_output))
        else:
            self.doc_work_obj.task_output = err_msg
            self.doc_work_obj.task_status = TASK_STATUS_PROCESSED_ERROR[0]
        self.doc_work_obj.save()

    # 删除临时文件
    def __clean_temp_file(self):
        if os.path.exists(self.local_src_file_path):
            os.remove(self.local_src_file_path)  # 删除本地源文件
        if os.path.exists(self.local_des_file_path):
            os.remove(self.local_des_file_path)  # 删除本地格式转换后的文件
        if os.path.exists(self.local_img_file_path):
            os.remove(self.local_img_file_path)  # 删除本地缩略图文件

    # 执行任务
    def execute(self):
        try:
            # 获取要处理的文档作品
            self.__get_an_available_work()
            if not self.doc_work_obj:
                logger.info("not found an available doc work")
                return True
            logger.debug("##################work_id[%d],work_file_id[%d],src_file_id[%d]###############################"
                         % (self.doc_work_obj.work_id, self.doc_work_obj.id, self.doc_work_obj.src_file_id))
            logger.debug("Begin process doc work [%d] " % self.doc_work_obj.id)

            # 下载文档文件
            self.__download_src_file()
            if not self.local_src_file_path:
                logger.error("[%d]download doc src file error" % self.doc_work_obj.id)
                raise Exception(u"[%d]下载原文档文件失败" % self.doc_work_obj.id)
            logger.debug("Have download doc file %s" % self.local_src_file_path)

            # 转换文档格式
            self.__change_file_format()
            logger.debug("[%d]Have convert the format" % self.doc_work_obj.id)

            # 上传格式转换完成后的文件
            self.__upload_local_files()
            logger.debug("[%d]Have upload format conversion complete file" % self.doc_work_obj.id)

            # 更新文档作品状态
            self.__update_task_status()
            logger.debug("[%d]End process doc work" % self.doc_work_obj.id)

            return False
        except Exception as ex:
            sErrInfo = traceback.format_exc()
            logger.error(sErrInfo)
            self.task_status = TASK_STATUS_PROCESSED_ERROR[0]
            if self.doc_work_obj:
                self.__update_task_status(ex.message)
            os.system("taskkill /f /im  WINWORD.EXE")
            os.system("taskkill /f /im  EXCEL.EXE")
            os.system("taskkill /f /im  POWERPNT.EXE")
            return False
        finally:
            self.__clean_temp_file()
            logger.debug("#################################################################")

    @staticmethod
    def execute_loop():
        task_work_num = WorkFileObj.objects.filter(task_status=TASK_STATUS_PROCESSING[0],
                                                   src_file__ext__in=support_doc_type, del_flag=FALSE_INT).count()
        if task_work_num > settings.CHANGE_DOC_FORMAT_TASK_WORK_NUM:
            logger.info("There are %d tasks executing" % task_work_num)
            return
        while True:
            task_obj = Change_Doc_Format()
            if task_obj.execute():
                logger.info("have process all")
                break


def change_doc_format_service():
    sleep_seconds = 1
    while True:
        try:
            time.sleep(sleep_seconds)
            sleep_seconds = 60 * 5
            Change_Doc_Format.execute_loop()
        except Exception as ex:
            sErrInfo = traceback.format_exc()
            logger.error(sErrInfo)
            logger.error("Exception in Service")
