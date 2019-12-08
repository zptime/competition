#!/bin/bash
# 说明：
# 1、本程序可以放在服务器任意目录，本程序名称也可以为任意命名
# 2、前置条件：
#             a）需要在最前面的一段代码中配置相关的待配置项
#             b）需要提前安装好GIT，并且更新代码时，ssh可以自动登录，不需要输入账号密码
#             c）安装好virtualenv，不需要创建git和工程目录
# 3、本程序利用了deploy脚本备份旧程序，请确保deploy.py在工程目录下
# 4、首次执行的时候，由于代码还没pull下来，导致程序备份和stop.sh时会报错，不必理会，更新一次后就恢复正常。
#
#

# 设置项目目录名，便于以后统一改
echo "[update] start"
# 待配置项：工程名，即工程目录名
project_name="competition_v3"
# 待配置项：工程目录，即工程在本服务器上的绝对路径
project_path="/opt/virt/$project_name/$project_name"
# 待配置项：git目录，此目录名必须和giturl的目录名相同
git_path="/opt/virt/$project_name/git/$project_name"
# 待配置项：工程giturl路径,仅首次执行时有用
git_url="ssh://192.168.100.21/data/git/hd/$project_name"
# 待配置项：git分支名称
git_branch_name="master"
# 待配置项：启停脚本绝对路径
project_sh_path="$project_path/deploy/"

# 检查入参
function help()
{
  echo "USAGE: $0 ENVNAME(dev/test/prod) [silent]" ;
  echo "----- dev  开发环境 -----" ;
  echo "----- test 测试环境 -----" ;
  echo "----- prod 生产环境 -----" ;
  echo " e.g.: $0 test" ;
  exit 1;
}

if [[ $1 != "dev" ]] && [[ $1 != "test" ]] && [[ $1 != "prod" ]] ; then
   help;
fi

if [[ $2 != "silent" ]] ; then
    read -s -n1 -p "即将自动备份并更新程序到git的$git_branch_name版本,并使用$1环境,请按y或回车继续！其它中断执行！"
    if [ $REPLY != "y" ]
    then
       echo
       exit
    else
       echo
    fi
fi

# 检查git目录是否存在，如果不存在，则先做git clone
if [ ! -d "$git_path" ]; then
  echo "[update] no git_path, create git dir"
  mkdir -p "$git_path"
  cd $git_path
  cd ..
  echo "[update] git clone start"
  git clone -b $git_branch_name $git_url
else
  echo "[update] git_path exist,no need clone"
fi

# 获取本文件绝对路径
sh_dir=`dirname $0`
cd $sh_dir
sh_dir=`pwd`
echo "[update] init OK"

# 更新代码
cd $git_path
echo "[update] git pull start..."
git pull
echo "[update] git pull OK"
cd $sh_dir

# 备份原程序
cd $project_path
echo "[update] backup start..."
python backup.py
echo "[update] backup OK"
cd $sh_dir

# 停应用
cd $project_sh_path
./stop.sh
cd $sh_dir

# 改名原目录，copy进来新的程序，copy老日志
echo "[update] del old code...."
cd $project_path
cd ..
mv $project_name old_project_dir
echo "[update] move old project dir OK"
cp -r $git_path $project_path
echo "[update] copy new project dir OK"
cp -r old_project_dir/log $project_path
echo "[update] copy oldlog to new project dir OK"
rm -rf old_project_dir
chmod -R 755 $project_path
echo "[update] del old code OK"
echo "[update] update code OK"

# 修改manage.py和wsgi.py
cd $project_path
echo "[update] modify manage.py"
sed -i "s/.settings/.settings.$1/g" manage.py
echo "[update] modify manage.py OK"
cd $project_name
echo "[update] modify wsgi.py"
sed -i "s/.settings/.settings.$1/g" wsgi.py
echo "[update] modify wsgi.py OK"
cd $sh_dir

# 创建gunicorn.conf的软链接
cd $project_path
if [ -f "gunicorn.conf" ]; then
 rm -rf gunicorn.conf
fi
ln -s gunicorn_$1.conf gunicorn.conf
echo "[update] link gunicorn.conf OK"

# 启应用
cd $project_sh_path
./start.sh
cd $sh_dir

echo "[update] finish OK"