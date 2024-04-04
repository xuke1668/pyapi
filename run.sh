#!/bin/bash
#set -x

source /etc/profile


function get_pid(){
    echo `ps aux|grep "${UWSGI} --uid "|grep ":${port} "|grep -v "grep"|awk '{print $2}' |xargs`
}

function Status(){
    pid=`get_pid`
    if [ "X$pid" != "X" ];then
        echo "uwsgi-${app_name} is running![pid:$pid]"
    else
        echo "uwsgi-${app_name} is not running!"
    fi
}

function Start(){
	pid=`get_pid`
    if [ "X$pid" != "X" ];then
        echo "uwsgi-${app_name} is running![pid:$pid]"
        return
    else
        ${UWSGI} --uid ${USER} -s ${host}:${port} --gevent 1000 -M -t 30 --pidfile ${pidfile} --chdir ${cur_dir} --env "APP_ENV=${app_env}" --env "APP_NAME=${app_name}" -w app:flask_app -d ${logfile} --logformat "${UWSGI_LOG_FORMAT}"
    fi
    sleep 1
    pid=`get_pid`
    if [ "X$pid" = "X" ];then
        echo "Start uwsgi-${app_name} failed"
        exit 1
    else
        echo "Start uwsgi-${app_name} success![pid:$pid]"
    fi
}

function Stop(){
    pid=`get_pid`
    if [ "X$pid" = "X" ];then
        echo "uwsgi-${app_name} is not running!"
    else
        ${UWSGI} --uid ${USER} --stop ${pidfile}
        if [ $? -ne 0 ];then
            echo "Stop uwsgi-${app_name} failed![pid:$pid]"
            exit 1
        else
            echo "Stop uwsgi-${app_name} success!"
        fi
    fi
}

function Reload(){
    pid=`get_pid`
    if [ "X$pid" = "X" ];then
        echo "uwsgi-${app_name} is not running!"
        Start
    else
        ${UWSGI} --uid ${USER} --reload ${pidfile}
        if [ $? -ne 0 ];then
            echo "Reload uwsgi-${app_name} failed![pid:$pid]"
            exit 1
        else
            pid=`get_pid`
            if [ "X$pid" != "X" ];then
                echo "Reload uwsgi-${app_name} success![pid:$pid]"
            else
                echo "Reload uwsgi-${app_name} failed!"
                exit 1
            fi
        fi
    fi
}


cur_dir="$(cd `dirname "$0"` && pwd)"

USER='uwsgi'
# id ${USER} >/dev/null 2>&1 || useradd -r -s /usr/sbin/nologin ${USER}   # 用户不存在时创建
# chown ${USER}. -R ${cur_dir}                  # 修改文件夹权限
UWSGI='/data/apps/python312/bin/uwsgi'          # 需要替换为实际的路径
UWSGI_LOG_FORMAT='"%(ltime)" "%(addr)" "%(uagent)" "%(method) %(uri)" %(cl)B %(status) %(rsize)B %(msecs)ms'

app_env='prod'
app_name='web'
host='127.0.0.1'
port='8890'
pidfile="/var/run/uwsgi-${app_name}-${app_env}.pid"
logfile="/var/log/uwsgi-${app_name}-${app_env}.log"

if [ "${1,,}" = "status" ]; then
    Status
elif [ "${1,,}" = "start" ]; then
    Start
elif [ "${1,,}" = "stop" ];then
    Stop
elif [ "${1,,}" = "reload" ];then
    Reload
elif [ "${1,,}" = "restart" ];then
    Stop && sleep 1 && Start
else
    echo -e "Usages:\n\tbash $0 [status|start|stop|reload|restart]"
fi
