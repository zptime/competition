# coding=utf-8
from models import *
from utils.const_err import SUCCESS
from utils.file_fun import *
from utils.public_fun import *
import zipfile
from applications.data.agents import upload_file
from django.core.files import File
import shutil
import traceback
from django.db import transaction
from task import resize_image_and_upload
import platform
if platform.system() == "Windows":
    from unrar import rarfile
else:
    import rarfile

logger = logging.getLogger(__name__)

MAX_PREVIEW_FILE_NUM = 16


class TooManyFiles(Exception):
    pass


class UnzipTask:
    def __init__(self):
        self.work_obj = None
        self.local_rar_file_path = ""
        self.work_dir_path = ""
        self.task_status = TASK_STATUS_PROCESSED_SUCCESS[0]

    # 获取一个要处理的作品
    @transaction.atomic
    def __get_an_available_work(self):
        self.work_obj = Work.objects.filter(task_status=TASK_STATUS_NOT_PROCESS[0], del_flag=FALSE_INT).\
            exclude(status=WORK_STATUS_NOT_UPLOAD[0]).first()
        now = datetime.datetime.now()
        if not self.work_obj:
            out_date = now - datetime.timedelta(minutes=TASK_PROCESSING_TIMEOUT_MINUTES)
            self.work_obj = Work.objects.filter(task_status=TASK_STATUS_PROCESSING[0], task_time__lt=out_date,
                                                del_flag=FALSE_INT).exclude(status=WORK_STATUS_NOT_UPLOAD[0]).first()
        if self.work_obj and self.work_obj.rar_file:
            self.work_obj.task_time = now
            self.work_obj.task_status = TASK_STATUS_PROCESSING[0]
            self.work_obj.save()


    # 下载作品文件
    def __download_rar_file(self):
        rar_file_obj = FileObj.objects.filter(id=self.work_obj.rar_file_id).first()
        if not rar_file_obj:
            raise Exception(u"[%d]没有找到对应的作品压缩文件" % self.work_obj.id)

        rar_file_url = get_image_url(rar_file_obj.url, abs=True)
        self.local_rar_file_path = download_file(rar_file_url)

    # 检查作品是否可以预览，并解压文件
    def __check_and_unzip_work(self):
        # 创建解压目录
        self.work_dir_path = os.path.join(settings.TEMP_DIR, self.work_obj.no)
        if os.path.exists(self.work_dir_path):
            shutil.rmtree(self.work_dir_path)
        os.mkdir(self.work_dir_path)

        # 解压文件
        unzip_file(self.local_rar_file_path, self.work_dir_path)

        # 检查文件数量是否超过可以预览的最大数量
        file_num = 0
        for parent, dir_names, file_names in os.walk(self.work_dir_path):  # 三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
            file_num += len(file_names)
        logger.debug("have unzip file and file_num=%d" % file_num)
        if file_num > MAX_PREVIEW_FILE_NUM:
            raise TooManyFiles()

    # 上传解压后的文件
    @transaction.atomic
    def __upload_unzip_files(self):
        for parent, dir_names, file_names in os.walk(self.work_dir_path):  # 三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
            for file_name in file_names:
                file_path = os.path.join(parent, file_name)  # 输出文件路径信息
                logger.debug("upload file %s " % file_path)
                with open(file_path, 'rb') as file_obj:
                    file_obj = File(file_obj, file_name)
                    resp_dict = upload_file(user=None, file_obj=file_obj, type_list=[],
                                            activity_id=self.work_obj.activity_id, prefix=self.work_obj.no)
                if resp_dict["c"] != SUCCESS[0]:
                    raise Exception(u"[%d]文件上传出错--%s" % (self.work_obj.id, resp_dict["m"]))
                file_info_list = resp_dict["d"]
                if not file_info_list:
                    if os.path.exists(self.work_dir_path):
                        shutil.rmtree(self.work_dir_path)
                    raise Exception(u"[%d]文件上传返回值为空" % self.work_obj.id)
                # 保存WorkFileObj
                file_info = file_info_list[0]
                src_file_id = file_info["id"]
                file_type = file_info["type"]
                if file_type == FILE_TYPE_IMG[0]:
                    resize_img_id = resize_image_and_upload(file_path, self.work_obj.activity_id, self.work_obj.no)
                    if not resize_img_id:
                        resize_img_id = src_file_id
                    WorkFileObj.objects.create(work=self.work_obj, src_file_id=src_file_id, des_file_id=src_file_id,
                                               img_file_id=resize_img_id, task_status=TASK_STATUS_PROCESSED_SUCCESS[0],
                                               task_output=u"图片文件不需要处理")
                elif file_type in NEED_PROCESS_TO_PREVIEW_FILE_TYPE:
                    WorkFileObj.objects.create(work=self.work_obj, src_file_id=file_info_list[0]["id"])
                else:
                    WorkFileObj.objects.create(work=self.work_obj, src_file_id=src_file_id,
                                               task_status=TASK_STATUS_PROCESSED_SUCCESS[0],
                                               task_output=u"文件格式不支持预览")


    # 更新任务状态
    @transaction.atomic
    def __update_task_status(self, msg=""):
        if self.task_status == TASK_STATUS_PROCESSED_SUCCESS[0]:
            if msg:
                self.work_obj.task_output = msg
            else:
                self.work_obj.task_output = u"作品解压任务完成"
            logger.info("[%d]%s" % (self.work_obj.id, self.work_obj.task_output))
        else:
            self.work_obj.task_output = msg
            self.work_obj.preview_status = WORK_PREVIEW_STATUS_NOT_SUPPORTED[0]
        self.work_obj.task_status = self.task_status
        self.work_obj.save()

    # 删除临时文件
    def __clean_temp_file(self):
        if os.path.exists(self.local_rar_file_path):
            os.remove(self.local_rar_file_path)  # 删除压缩包
        if os.path.exists(self.work_dir_path):
            shutil.rmtree(self.work_dir_path)  # 删除解压文件夹

    # 执行任务
    def execute(self):
        try:
            # 获取要处理的作品
            self.__get_an_available_work()
            if not self.work_obj:
                logger.info("not found an available work to unzip")
                return True
            logger.debug("###########################work_id[%d]######################################" % self.work_obj.id)
            logger.debug("Begin process work %s " % self.work_obj.no)

            # 下载作品文件
            self.__download_rar_file()
            if not self.local_rar_file_path:
                logger.error("download rar file error")
                raise Exception("download rar file error")
            logger.debug("Have download rar file %s" % self.local_rar_file_path)

            # 解压作品文件
            self.__check_and_unzip_work()
            if not self.work_dir_path:
                logger.error("[]unzip rar file error" % self.work_obj.id)
                raise Exception("unzip rar file error")
            logger.debug("Have unzip dir path %s" % self.work_dir_path)

            # 上传解压后的作品
            self.__upload_unzip_files()
            logger.debug("Have upload all unzip file%s " % self.work_obj.no)

            # 更新作品状态
            self.__update_task_status()
            logger.debug("End process work %s" % self.work_obj.no)
            return False
        except TooManyFiles as ex:
            logger.info("Too many files")
            self.task_status = TASK_STATUS_PROCESSED_SUCCESS[0]
            if self.work_obj:
                self.__update_task_status(u"作品中包含文件数量过多，不支持预览")
            return False
        except Exception as ex:
            sErrInfo = traceback.format_exc()
            logger.error(sErrInfo)
            self.task_status = TASK_STATUS_PROCESSED_ERROR[0]
            if self.work_obj:
                self.__update_task_status(ex.message)
            return False
        finally:
            self.__clean_temp_file()
            logger.debug("#################################################################")

    @staticmethod
    def execute_loop():
        task_work_num = Work.objects.filter(task_status=TASK_STATUS_PROCESSING[0], del_flag=FALSE_INT).count()
        if task_work_num > settings.UNZIP_TASK_WORK_NUM:
            logger.info("There are %d tasks executing" % task_work_num)
            return

        while True:
            task_obj = UnzipTask()
            if task_obj.execute():
                logger.info("have process all")
                break


def zip_extract_all(zip_filename, extract_dir, filename_encoding='GBK'):
    zf = zipfile.ZipFile(zip_filename, 'r')
    if isinstance(extract_dir, unicode):
        print "convert dir encode"
        extract_dir = extract_dir.encode("utf-8")
    for file_info in zf.infolist():
        filename = file_info.filename
        if not isinstance(file_info.filename, unicode):
            filename = unicode(filename, filename_encoding)
        filename.encode("utf8")
        # logger.debug('zip_extract_all filename is %s dir is %s' % (filename, extract_dir))
        output_filename = os.path.join(extract_dir, filename)
        output_file_dir = os.path.dirname(output_filename)
        if not os.path.exists(output_file_dir):
            os.makedirs(output_file_dir)
        if os.path.isdir(output_filename):
            continue
        with open(output_filename, 'wb') as output_file:
            shutil.copyfileobj(zf.open(file_info.filename), output_file)
    zf.close()


def unzip_file(rar_file_path, dir_path):
    type, ext = get_file_type(rar_file_path)
    # 获取压缩包中的文件列表
    rar = None
    if ext == FILE_EXT_RAR:
        try:
            rar = rarfile.RarFile(rar_file_path)
        except rarfile.BadRarFile:
            rar = zipfile.ZipFile(rar_file_path)
    elif ext == FILE_EXT_ZIP:
        try:
            rar = zipfile.ZipFile(rar_file_path)
        except zipfile.BadZipfile:
            rar = rarfile.RarFile(rar_file_path)
    else:
        logger.error("file ext is not zip or rar %s" % rar_file_path)

    # 解压文件
    if not os.path.exists(dir_path):
        logger.error("unzip_file() dir_path %s not exists" % dir_path)

    if isinstance(rar, rarfile.RarFile):
        rar.extractall(dir_path)
    else:
        zip_extract_all(rar_file_path, dir_path)
    os.remove(rar_file_path)

    for parent, dir_names, file_names in os.walk(dir_path):  # 三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
        for file_name in file_names:
            file_path = os.path.join(parent, file_name)  # 输出文件路径信息
            type, ext = get_file_type(file_name)
            if type == FILE_TYPE_ZIP[0]:
                unzip_file(file_path, parent)