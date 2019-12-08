# -*- coding: utf-8 -*-
import fnmatch

import datetime

import os

from django.conf import settings
from applications.upload_resumable.err_code import UPLOAD_ERR_PART_SUCCESS, UPLOAD_ERR_COMPLETE_SUCCESS, UPLOAD_ERR_FILE_MD5_ERR_ERR
from applications.upload_resumable.storage.file_storage import FileStorage
from applications.upload_resumable.utils_data import md5sum, generate_file_md5, logger
from utils.store_file import must_exist_folder


class ResumableFile(object):
    def __init__(self, kwargs, user):
        self.storage = FileStorage('media')
        self.chunk_storage = FileStorage('tmp_file')
        self.kwargs = kwargs
        self.chunk_suffix = "_part_"
        self.user_id = str(user.id) if user.id else ''
        self.cur_user_id = str(user.id) if user.id else ''
        # self.dir_name = str(user.school_id)
        year_str = str(datetime.datetime.now().year)
        must_exist_folder(os.path.join(settings.TEMP_DIR, year_str))
        self.dir_name = year_str

    @property
    def chunk_file_path(self):
        name = "%s%s%s" % (self.filename,
                           self.chunk_suffix,
                           self.kwargs.get('resumableChunkNumber').zfill(4))
        chunk_path = os.path.join(self.chunk_storage.dir, name)
        return chunk_path

    @property
    def chunk_exists(self):
        """Checks if the requested chunk exists."""
        # name = "%s%s%s" % (self.filename,
        #                    self.chunk_suffix,
        #                    self.kwargs.get('resumableChunkNumber').zfill(4))
        # chunk_path = os.path.join(self.chunk_storage.dir, name)
        chunk_path = self.chunk_file_path
        if not self.chunk_storage.exists(chunk_path):
            return False
        chunk_size = int(self.kwargs.get('resumableCurrentChunkSize'))
        if not (self.chunk_storage.size(chunk_path) == chunk_size):
            self.chunk_storage.delete(chunk_path)
            return False
        return True

    def chunk_names(self):
        """Iterates over all stored chunks and yields their names."""
        dir_path = os.path.dirname(self.chunk_file_path)
        chunk_file_names = sorted(self.chunk_storage.listdir(dir_path)[1])

        pattern = '%s%s*' % (self.filename.split('/')[-1], self.chunk_suffix)
        for name in chunk_file_names:
            if fnmatch.fnmatch(name, pattern):
                yield os.path.join(dir_path, name)

    def chunks(self):
        """Yield the contents of every chunk, FileSystemStorage.save compatible
        """
        for name in self.chunk_names():
            yield self.chunk_storage.open(name).read()

    def delete_chunks(self):
        [self.chunk_storage.delete(chunk) for chunk in self.chunk_names()]

    @property
    def file_md5sum(self):
        """Gets the file total md5sum."""
        return self.kwargs.get('totalFileMd5sum', "")

    @property
    def is_exist(self):
        """Check upload file is exist."""
        return self.storage.exists(self.file_path)

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
    def file_path(self):
        return self.storage.get_file_path(self.filename)

    @property
    def is_complete(self):
        """Checks if all chunks are allready stored."""

        return int(self.kwargs.get('resumableTotalSize')) == self.size

    def process_chunk(self, file):
        chunk_path = self.chunk_file_path
        if not self.chunk_exists:
            self.chunk_storage.save(chunk_path, file)
        return UPLOAD_ERR_PART_SUCCESS

    @property
    def size(self):
        """Gets chunks size."""
        size = 0
        for chunk in self.chunk_names():
            size += self.chunk_storage.size(chunk)
        return size

    def process_file(self):
        """Process the complete file.
        """
        self.storage.save(self.file_path, self)
        if self.file_md5sum and not self.check_whole_md5():
            return UPLOAD_ERR_FILE_MD5_ERR_ERR
        self.delete_chunks()
        return UPLOAD_ERR_COMPLETE_SUCCESS

    def check_whole_md5(self):
        src_file_md5 = self.file_md5sum
        md5 = generate_file_md5(self.file_path)
        if src_file_md5 != md5:
            logger.error("check_whole_md5 error src_md5=%s, dst_md5=%s", src_file_md5, md5)
            return False
        else:
            return True


def get_file_md5(file_path):
    md5 = generate_file_md5(file_path)
    return md5
