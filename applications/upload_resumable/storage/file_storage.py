# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.files.storage import FileSystemStorage

import os
import logging
import hashlib
import errno
import shutil


logger = logging.getLogger(__name__)


class FileStorage(FileSystemStorage):
    def __init__(self, dir_name=""):
        if dir_name:
            self.dirname = dir_name
        else:
            self.dirname = settings.FILE_STORAGE_DIR_NAME
        self.dir = os.path.join(settings.BASE_DIR, self.dirname)
        super(FileStorage, self).__init__(location=self.dir)
        # logger.info("init File Storage dir = %s" % self.dir)

    def get_relative_url(self, path):
        url = "/" + self.dirname + "/" + path
        return url

    def upload_file_obj(self, src_file_obj, obj_path):
        md5sum = ""
        try:
            hasher = hashlib.md5()
            dst_file_path = os.path.join(self.dir, obj_path)
            dir_path = os.path.dirname(dst_file_path)
            mkdir_p(dir_path)
            with open(dst_file_path, 'wb') as f:
                for chunk in src_file_obj.chunks(5 * 2 ** 20):
                    if chunk:   # filter out keep-alive new chunks
                        hasher.update(chunk)
                        f.write(chunk)
            md5sum = hasher.hexdigest()
        except Exception, ex:
            logger.exception("Could not write file '%s':  %s" % (src_file_obj, ex))
        finally:
            return md5sum

    def upload_local_file(self, src_file_path, obj_path):
        md5sum = ""
        try:
            dst_file_path = os.path.join(self.dir, obj_path)
            if src_file_path == dst_file_path:
                return
            dir_path = os.path.dirname(dst_file_path)
            mkdir_p(dir_path)
            shutil.copy(src_file_path, dst_file_path)
            md5sum = generate_file_md5(dst_file_path)
        except Exception, ex:
            logger.exception("Could not write file '%s':  %s" % (src_file_path, ex))
        finally:
            return md5sum

    def get_file_path(self, name):
        if os.path.isabs(name):
            return name
        else:
            return os.path.join(self.dir, name)

    # 设置权限
    def set_mode(self, obj_path, public):
        try:
            file_path = os.path.join(self.dir, obj_path)
            if public:
                os.chmod(file_path, 0644)
            else:
                os.chmod(file_path, 0000)
        except Exception as ex:
            logger.error("set mode error '%s'", obj_path)
            return False
        return True

    def exists(self, name):
        file_path = self.get_file_path(name)
        return super(FileStorage, self).exists(file_path)

    def delete(self, name):
        file_path = self.get_file_path(name)
        return super(FileStorage, self).delete(file_path)

    def size(self, name):
        file_path = self.get_file_path(name)
        return super(FileStorage, self).size(file_path)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def generate_file_md5(filepath, blocksize=2**20):
    m = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()
