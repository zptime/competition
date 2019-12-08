# -*- coding: utf-8 -*-
import os

from applications.upload_resumable.err_code import *
from applications.upload_resumable.utils_data import *
from applications.upload_resumable.utils_upload import upload_lock_acquire, upload_lock_release
from utils.const_def import MD5_COMPUTE_STATUS_GETFILEERR


class ResumableFile(object):
    def __init__(self, kwargs, user):
        self.storage = get_storage_obj()
        self.kwargs = kwargs
        self.user_id = str(user.id)
        # dir_name根据业务定制
        # self.dir_name = str(user.school_id)
        # self.dir_name = datetime.datetime.now().strftime("%Y%m")
        self.dir_name = str(kwargs.get("activity_id", 0))
        if self.dir_name == 0:
            logger.warn('find resumable file upload, but activity_id is ZERO. user_id is %s' % str(user.id))
        self.cur_user_id = str(kwargs.get("cur_user_id", 0))
        self.mp = None
        self.is_exist = False

        # 初始化mp 和 is_exist
        total_size = int(self.kwargs.get('resumableTotalSize'))
        if self.storage.exists(self.filename) and total_size == self.storage.size(self.filename):
            self.is_exist = True
        else:
            self.mp = self.storage.locate_mp(self.filename)
            if self.mp is None:
                self.mp = self.init_multipart_upload()
            if not self.mp:
                raise Exception("ERROR: not found mp or init mp %s" % self.filename)

    @property
    def chunk_exists(self):
        """Checks if the requested chunk exists."""
        return self.storage.part_exists(obj_path=self.filename,
                                        part_num=int(self.kwargs.get('resumableChunkNumber')),
                                        size=int(self.kwargs.get('resumableCurrentChunkSize'),),
                                        found_mp=self.mp
                                        )

    @property
    def part_num(self):
        """Gets the part_num."""
        return int(self.kwargs.get('resumableChunkNumber'))

    @property
    def src_filename(self):
        """Gets the filename."""
        filename = self.kwargs.get('resumableFilename')
        if '/' in filename or len(filename) > 100:
            raise Exception('Invalid filename')
        return filename

    @property
    def total_size(self):
        """Gets the filename."""
        return self.kwargs.get('resumableTotalSize')

    @property
    def md5sum(self):
        """Gets the chunk md5sum."""
        return self.kwargs.get('md5sum')

    @property
    def file_md5sum(self):
        """Gets the file total md5sum."""
        return self.kwargs.get('totalFileMd5sum', "")

    # @property
    # def dir_name(self):
    #     """Gets the dir_name."""
    #     return self.kwargs.get('dir_name')

    @property
    def filename(self):
        """Gets the save filename."""
        filename = self.kwargs.get('resumableFilename')
        if '/' in filename or len(filename) > 100:
            raise Exception('Invalid filename')
        ext = os.path.splitext(filename)[-1].lower()
        str = "%s_%s_%s" % (
            self.user_id,
            self.kwargs.get('resumableTotalSize'),
            filename,
        )
        full_name = self.dir_name + "/" + md5sum(str) + ext
        return full_name


    @property
    def is_complete(self):
        """Checks if all chunks are allready stored."""
        total_chunks = int(self.kwargs.get('resumableTotalChunks'))
        total_parts = self.storage.total_part_count(self.filename, self.mp)
        if total_chunks == total_parts:
            return True
        elif total_chunks > total_parts:
            return False
        else:
            logger.error("total_chunks < total_parts")
            self.storage.cancel_upload(self.filename, self.mp)
            raise Exception("total_chunks < total_parts")

    def process_chunk(self, file):
        part_num = int(self.kwargs.get('resumableChunkNumber'))
        size = int(self.kwargs.get('resumableTotalSize'))
        md5 = self.kwargs.get('md5sum', "")

        is_available, code = upload_lock_acquire(self.filename, part_num)
        if is_available:
            if self.storage.upload_part(content=file, obj_path=self.filename, part_num=part_num, size=size, found_mp=self.mp, md5=md5):
                # upload_lock_finish(self.filename, part_num)
                return UPLOAD_ERR_PART_SUCCESS
            else:
                upload_lock_release(self.filename, part_num)
                return UPLOAD_ERR_PART_UPLOAD_ERROR
        else:
            return UPLOAD_ERR_CANNOT_LOCK_ERROR

    def process_file(self):
        is_available, code = upload_lock_acquire(self.filename, COMPLETE_UPLOAD_PART_NUM)
        if is_available:
            if self.storage.complete_upload(self.filename, self.mp):
                # upload_lock_finish(self.filename, COMPLETE_UPLOAD_PART_NUM)
                if self.file_md5sum and not self.check_whole_md5():
                    self.storage.cancel_upload(self.filename, self.mp)
                    self.storage.delete(self.filename)
                    upload_lock_release(self.filename)
                    return UPLOAD_ERR_FILE_MD5_ERR_ERR
                return UPLOAD_ERR_COMPLETE_SUCCESS
            else:
                upload_lock_release(self.filename, COMPLETE_UPLOAD_PART_NUM)
                return UPLOAD_ERR_COMPLETE_UPLOAD_ERROR
        return UPLOAD_ERR_CANNOT_LOCK_ERROR

    def init_multipart_upload(self):
        is_available, code = upload_lock_acquire(self.filename, INITIATE_UPLOAD_PART_NUM)
        if code == UPLOAD_ACQUIRE_FINISH_TIME_OUT:
            self.storage.cancel_upload(self.filename, self.mp)
        if is_available:
            mp = self.storage.init_multipart_upload(self.filename)
            if not mp:
                upload_lock_release(self.filename, INITIATE_UPLOAD_PART_NUM)
            else:
                # upload_lock_finish(self.filename, INITIATE_UPLOAD_PART_NUM)
                return mp
        return None

    def check_whole_md5(self):
        tmp_file_name = self.filename.split("/")[-1]
        tmp_file_name += "_tmp"
        tmp_file_path = os.path.join(settings.TEMP_DIR, tmp_file_name)
        ret = self.storage.get_contents_to_filename(self.filename, tmp_file_path)
        if not ret:
            return ret
        src_file_md5 = self.file_md5sum
        md5 = generate_file_md5(tmp_file_path)
        os.remove(tmp_file_path)
        if src_file_md5 != md5:
            logger.error("check_whole_md5 error src_md5=%s, dst_md5=%s", src_file_md5, md5)
            return False
        else:
            return True


def get_file_md5(file_path):
    """
    入参路径为s3上路径，会将文件进行下载，计算完md5后再进行删除。
    :param file_path:
    :return:
    """
    file_name = file_path.split("/")[-1]
    tmp_file_name = file_name + "_" + get_nonce(6)
    tmp_file_path = os.path.join(settings.TEMP_DIR, tmp_file_name)
    storage = get_storage_obj()
    ret = storage.get_contents_to_filename(file_path, tmp_file_path)
    if not ret:
        return MD5_COMPUTE_STATUS_GETFILEERR

    md5 = generate_file_md5(tmp_file_path)
    os.remove(tmp_file_path)
    return md5

