#!/bin/bash
# 请先配置下面的待配置项
# 使用方法:
# buildfrontapp.sh [当前编译用户]
# eg. ./buildfrontapp.sh liukai

# 设置项目目录名，便于以后统一改
echo "[update] start"
# 待配置项：工程名，即工程目录名
project_name="competition_v3"
# 待配置项：虚拟环境完整路径
vitualenv_path="/opt/virt/$project_name"
# 待配置项：工程目录，即工程在本服务器上的绝对路径
project_path="$vitualenv_path/$project_name"
# 待配置项：前端源码目录
frontapp_path="$project_path/frontapp"
# 待配置项：首页文件路径
index_path="$project_path/templates/page/index.html"


# 检查是否正在编译
if [ ! -f "$vitualenv_path/buildlock" ]; then
  echo ""
else
  echo "当前有人正在编译！不能重复编译！"
  cat "$vitualenv_path/buildfrontapp.log"
  exit -1
fi

# 检查完成编译锁，先删除2分钟前的锁,再检查锁是否存在
find . -maxdepth 1 -amin +2 -name buildfinishlock -exec rm {} \;
if [ ! -f "$vitualenv_path/buildfinishlock" ]; then
  echo ""
else
  echo "刚刚才编译完成，不允许再次编译！"
  cat "$vitualenv_path/buildfrontapp.log"
  exit -1
fi


echo 编译锁定
cd $vitualenv_path
touch buildlock

# 开始编译
date > $index_path
echo "前端正在编译发布，请稍候！发布人：$1 " >> $index_path
echo -e "\n<br \>" >> $index_path
cd $project_path
echo 开始编译时间： > $vitualenv_path/buildfrontapp.log
date >> $vitualenv_path/buildfrontapp.log
# ls -lrt >> $vitualenv_path/buildfrontapp.log
echo 当前编译人：$1 >> $vitualenv_path/buildfrontapp.log
# sleep 2


cd $frontapp_path
echo 正在安装包，请稍等 >> $vitualenv_path/buildfrontapp.log
date >> $index_path
echo 正在安装包，请稍等 >> $index_path
echo -e "\n<br \>" >> $index_path
cnpm install >> $vitualenv_path/buildfrontapp.log
echo 安装包已结束，正在编译前端代码，请稍等 >> $vitualenv_path/buildfrontapp.log
date >> $index_path
echo 安装包已结束，正在编译前端代码，请稍等 >> $index_path
echo -e "\n<br \>" >> $index_path

cnpm run build >> $vitualenv_path/buildfrontapp.log
cat $vitualenv_path/buildfrontapp.log

echo 结束编译时间： >> $vitualenv_path/buildfrontapp.log
date >> $vitualenv_path/buildfrontapp.log
echo 本次编译两分钟内不允许重复编译，如需强制编译，请先清除锁定 >> $vitualenv_path/buildfrontapp.log

# 增加编译完成锁，上次编译2分钟内不允许再次编译
cd $vitualenv_path
touch buildfinishlock

# 解除正在编译锁
cd $vitualenv_path
rm -f buildlock
