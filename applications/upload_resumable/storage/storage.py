from django.conf import settings
from object_storage import ObjectStorage
from file_storage import FileStorage

OBJECT_STORAGE_OBJ = None


def get_storage_obj(dir_name=""):
    global OBJECT_STORAGE_OBJ
    if OBJECT_STORAGE_OBJ is None:
        if settings.DATA_STORAGE_USE_S3:
            OBJECT_STORAGE_OBJ = ObjectStorage()
        else:
            OBJECT_STORAGE_OBJ = FileStorage(dir_name)
    return OBJECT_STORAGE_OBJ
