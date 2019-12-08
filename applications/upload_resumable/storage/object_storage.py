# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.files import File

from boto.s3.connection import S3Connection
from boto.s3.connection import OrdinaryCallingFormat

from boto.exception import *
from boto.s3.key import Key
import time
import StringIO
import base64
import binascii
import traceback
import logging
import hashlib
import os
import math
import filechunkio
import httplib

logger = logging.getLogger(__name__)


def get_operator():
    global operator
    if not operator:
        operator = ObjectStorage()
    return operator


class ObjectStorage():
    def __init__(self, access_key="", secret_key="", host="", bucket_name="", location=""):
        logger.info("connecting to S3 Server...")
        logger.info("if there's no [connected to S3 Server] message, please check the network to S3 Server")
        self.access_key = access_key or settings.AWS_ACCESS_KEY_ID
        self.secret_key = secret_key or settings.AWS_SECRET_ACCESS_KEY
        self.host = host or settings.AWS_S3_HOST
        self.port = settings.AWS_S3_PORT or 80
        self.bucket_name = bucket_name or settings.AWS_STORAGE_BUCKET_NAME
        self.location = location

        self.conn = S3Connection(aws_access_key_id=self.access_key,
                                 aws_secret_access_key=self.secret_key,
                                 is_secure=False,
                                 host=self.host,
                                 port=self.port,
                                 calling_format=OrdinaryCallingFormat())
        self.bucket = self._get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        logger.info("connected to S3 Server......")

    def _get_bucket(self, bucket_name):
        """ Sometimes a handle to a bucket is not established right away so try
        it a few times. Raise error if connection is not established. """
        for i in range(5):
            try:
                bucket = self.conn.get_bucket(bucket_name)
                logger.debug("Using cloud object store with bucket '%s'", bucket.name)
                return bucket
            except S3ResponseError:
                try:
                    logger.debug("Bucket not found, creating s3 bucket with handle '%s'", bucket_name)
                    self.conn.create_bucket(bucket_name)
                except S3ResponseError:
                    logger.exception("Could not get bucket '%s', attempt %s/5", bucket_name, i + 1)
                    time.sleep(2)
        # All the attempts have been exhausted and connection was not established,
        # raise error
        raise S3ResponseError

    def get_relative_url(self, path):
        url = "/" + self.bucket_name + "/" + path
        return url

    # radosgw 存储会出现文件上传成功后，无法正常下载的情况，通过该函数可以检查文件是否可以正常下载
    def check_file_download(self, url):
        url = self.get_relative_url(url)
        conn = httplib.HTTPConnection(host=self.host, port=self.port)
        conn.request("GET", url, headers={'Range': 'bytes=0-0'})
        resp = conn.getresponse()
        if resp.status >= 300:
            msg = "[check_file_download] error download url=%s code=%d" % (url, resp.status)
            logger.error(msg)
            return False
        return True

    # 设置权限
    def set_mode(self, obj_path, public):
        try:
            if public:
                self.bucket.set_acl('public-read', obj_path)
            else:
                self.bucket.set_acl('private', obj_path)
        except Exception as ex:
            logger.error("set mode error '%s'", obj_path)
            return False
        return True

    def exists(self, obj_path):
        exists = False
        try:
            # A hackish way of testing if the obj_path is a folder vs a file
            is_dir = obj_path[-1] == '/'
            if is_dir:
                keyresult = self.bucket.get_all_keys(prefix=obj_path)
                if len(keyresult) > 0:
                    exists = True
                else:
                    exists = False
            else:
                key = Key(self.bucket, obj_path)
                exists = key.exists()
        except S3ResponseError:
            logger.exception("Trouble checking existence of S3 key '%s'", obj_path)
            return False
        if obj_path[0] == '/':
            raise Exception
        return exists

    def copy(self, src_obj_path, dst_obj_path):
        try:
            src_key = self.bucket.get_key(src_obj_path)
            if not src_key:
                logger.error("copy error: src_key %s not exist", src_obj_path)
            dst_key = src_key.copy(dst_bucket=settings.AWS_STORAGE_BUCKET_NAME, dst_key=dst_obj_path, preserve_acl=True)
            if dst_key and self.check_file_download(dst_obj_path):
                logger.debug("copy success src_key %s to dst_key %s", src_obj_path, dst_obj_path)
                return True
            else:
                logger.error("copy error: src_key %s to dst_key %s", src_obj_path, dst_obj_path)
        except S3ResponseError:
            logger.exception("Could not copy src_key %s to dst_key %s", src_obj_path, dst_obj_path)
        return False

    def delete(self, obj_path, entire_dir=False):
        try:
            if entire_dir:
                results = self.bucket.get_all_keys(prefix=obj_path)
                for key in results:
                    logger.debug("Deleting key %s", key.name)
                    key.delete()
                return True
            else:
                if self.exists(obj_path):
                    key = Key(self.bucket, obj_path)
                    logger.debug("Deleting key %s", key.name)
                    key.delete()
                    return True
        except S3ResponseError:
            logger.exception("Could not delete key '%s' from S3", obj_path)
        return False

    def get_contents_to_filename(self, obj_path, dst_file_path):
        try:
            src_key = self.bucket.get_key(obj_path)
            src_key.get_contents_to_filename(dst_file_path)
        except Exception, ex:
            logger.exception("Download error key '%s' from S3", obj_path)
            return False
        return True

    def upload_file_obj(self, src_file_obj, obj_path):
        hasher = hashlib.md5()
        try:
            key = self.bucket.new_key(obj_path)
            mp = self.bucket.initiate_multipart_upload(obj_path)
            i = 0
            # s3 multipart upload should be larger than 5MB
            for chunk in src_file_obj.chunks(5 * 2 ** 20):
                size = len(chunk)
                hasher.update(chunk)
                i += 1
                fp = StringIO.StringIO(chunk)
                mp.upload_part_from_file(fp, part_num=i, md5=key.compute_md5(fp, size))
            mp.complete_upload()
            self.bucket.set_acl('public-read', obj_path)
            if self.check_file_download(obj_path):
                return hasher.hexdigest()
        except S3ResponseError:
            logger.exception("Could not upload key '%s' to S3", obj_path)
        except Exception, ex:
            logger.exception("Could not read source to key '%s' to S3: %s" % (obj_path, ex))
        return None

    def upload_local_file(self, file_path, obj_path):
        hasher = hashlib.md5()
        try:
            key = self.bucket.new_key(obj_path)
            mp = self.bucket.initiate_multipart_upload(obj_path)
            chunk_size = 5 * 2 ** 20
            file_size = os.stat(file_path).st_size
            # s3 multipart upload should be larger than 5MB
            chunk_count = int(math.ceil(file_size / float(chunk_size)))
            for i in range(chunk_count):
                offset = chunk_size * i
                bytes = min(chunk_size, file_size - offset)
                with filechunkio.FileChunkIO(file_path, 'r', offset=offset, bytes=bytes) as fp:
                    mp.upload_part_from_file(fp, part_num=i + 1)
            mp.complete_upload()
            self.bucket.set_acl('public-read', obj_path)
            if self.check_file_download(obj_path):
                return hasher.hexdigest()
        except S3ResponseError:
            logger.exception("Could not upload key '%s' to S3", obj_path)
        except Exception, ex:
            logger.exception("Could not read source to key '%s' to S3: %s" % (obj_path, ex))
        return None

    def size(self, obj_path):
        try:
            key = self.bucket.get_key(obj_path)
            if key:
                return key.size
        except S3ResponseError, ex:
            logger.error("Could not get size of key '%s' from S3: %s" % (obj_path, ex))
        except Exception, ex:
            logger.error("Could not get reference to the key object '%s'; returning -1 for key size: %s" % (obj_path, ex))
        return -1

    def last_modified(self, obj_path):
        try:
            key = self.bucket.get_key(obj_path)
            if key:
                return key.last_modified
        except S3ResponseError, ex:
            logger.error("Could not get last_modified of key '%s' from S3: %s" % (obj_path, ex))
        except Exception, ex:
            logger.error("Could not get reference to the key object '%s'; %s" % (obj_path, ex))
        return None

    def locate_mp(self, obj_path):
        found_mp = None
        try:
            mp_list = self.bucket.list_multipart_uploads(key_marker=obj_path)
            for mp in mp_list:
                if mp.key_name != obj_path:
                    continue
                elif found_mp is not None:
                    logger.warn("mp more than one %s" % obj_path)
                #     mp.cancel_upload()
                else:
                    found_mp = mp
        except Exception, ex:
            logger.error("Could not locate mp to the key object '%s'; %s" % (obj_path, ex))
        return found_mp

    def init_multipart_upload(self, obj_path):
        try:
            logger.debug("before init")
            ret = self.bucket.initiate_multipart_upload(obj_path)
            logger.debug("after init")
            return ret
        except Exception, ex:
            logger.error("Could not init multi part upload '%s'; %s" % (obj_path, ex))
        return None

    def locate_part(self, mp, part_num):
        found_part = None
        try:
            parts = mp.get_all_parts()
            for part in parts:
                # part_number is integer type
                if part.part_number == part_num:
                    found_part = part
                    break
        except Exception, ex:
            logger.error("cannot locate part part_num '%d'; %s" % (part_num, ex))
        return found_part

    def part_exists(self, obj_path, part_num, size, md5="", found_mp=None):
        if found_mp is None:
            return False
        parts = found_mp.get_all_parts()
        found_part = None
        for part in parts:
            # part_number is integer type
            if part.part_number == part_num:
                found_part = part
                break
        if found_part is None:
            return False
        if found_part.size != size:
            return False
        if len(md5) > 0:
            if found_part.etag != md5:
                return False
        return True

    def upload_part(self, content, obj_path, part_num, size, found_mp, md5):
        key = None
        try:
            fp = File(content)
            logger.debug("before upload")
            key = found_mp.upload_part_from_file(fp, part_num=part_num, md5=(md5, base64.b64encode(binascii.unhexlify(md5))))
            logger.debug("after upload")
        except S3ResponseError, ex:
            sErrInfo = traceback.format_exc()
            logger.error(sErrInfo)
            if "BadDigest" in ex.body:
                logger.warn("md5 check error")
            else:
                logger.warn("not md5 check error")
        except Exception, ex:
            logger.error("Could not upload part '%s'; %s" % (obj_path, ex))
        return key

    def total_part_count(self, obj_path, found_mp):
        part_num = 0
        try:
            if found_mp is not None:
                parts = found_mp.get_all_parts()
                part_num = len(parts)
        except Exception, ex:
            logger.error("Could not complete upload the key object '%s'; %s" % (obj_path, ex))
        return part_num

    def complete_upload(self, obj_path, found_mp):
        try:
            if found_mp is None:
                return False
            else:
                logger.debug("before complete")
                found_mp.complete_upload()
                self.bucket.set_acl('public-read', obj_path)
                logger.debug("after complete")
                return True
        except Exception, ex:
            logger.error("Could not complete upload the key object '%s'; %s" % (obj_path, ex))
            return False

    def cancel_upload(self, obj_path, found_mp):
        logger.info("cancel upload %s" % obj_path)
        try:
            if found_mp is None:
                return False
            else:
                found_mp.cancel_upload()
                return True
        except Exception, ex:
            logger.error("Could not cancel upload the key object '%s'; %s" % (obj_path, ex))
            return False