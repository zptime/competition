# -*- coding: utf-8 -*-

import sys
import os
import shutil
import datetime
import tarfile


# 这些路径将不被备份
exclude = ['log', 'temp', 'media', 'deploy']

# 备份路径
backup_home = '/home/backup/'

current_path = sys.path[0]
project_name = current_path.split('/')[-1]


def tar(gz_path, folder_path):
    """
        压缩 .tar.gz
    """
    tar = tarfile.open(gz_path, "w:gz")
    for root, dir, files in os.walk(folder_path):
        for file in files:
            fullpath = os.path.join(root, file)
            tar.add(fullpath, arcname=(root.replace(folder_path, project_name)+'/'+file))
    tar.close()


def backup():
    """
        备份原部署文件
    """
    backup_path = os.path.join(backup_home, project_name+'_'+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(backup_path)

    # 将原部署文件复制到备份区域，并忽略下述文件：
    # （1）.pyc, .开头的文件夹
    # （2）exclude配置的所有文件夹或者文件
    for each_file_or_folder in os.listdir(current_path):
        if each_file_or_folder in exclude or each_file_or_folder.startswith('.'):
            continue
        else:
            abs_path = os.path.join(current_path, each_file_or_folder)
            if os.path.isdir(abs_path):
                shutil.copytree(abs_path, os.path.join(backup_path, each_file_or_folder), symlinks=True, ignore=shutil.ignore_patterns('*.pyc',))
            elif os.path.isfile(abs_path) and not each_file_or_folder.endswith('.pyc'):
                shutil.copyfile(abs_path, os.path.join(backup_path, each_file_or_folder))
            else:
                continue
    print '[BACKUP] Copy file done.'

    # 打包备份文件为.tar.gz
    tar(os.path.join(backup_home, project_name+'_'+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+'.tar.gz')
            , backup_path)
    print '[BACKUP] Make .tar.gz package done.'

    # 删除临时文件夹
    shutil.rmtree(backup_path)
    print '[BACKUP] Delete tmp files done.'
    print '[BACKUP] Backup finish!'


if __name__ == '__main__':
    backup()







