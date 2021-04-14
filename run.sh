#!/bin/bash
#set -x

source /etc/profile


function get_pid(){
    echo `ps aux|grep "${UWSGI} --uid "|grep ":${port} "|grep -v "grep"|awk '{print $2}' |xargs`
}

function Status(){
    pid=`get_pid`
    if [ "X$pid" != "X" ];then
        echo "uwsgi-${app} is running![$pid]"
    else
        echo "uwsgi-${app} is not running!"
    fi
}

function Start(){
	pid=`get_pid`
    if [ "X$pid" != "X" ];then
        echo "uwsgi-${app} is running![$pid]"
        return
    else
        ${UWSGI} --uid ${USER} -s ${host}:${port} --gevent 1000 -M -t 30 --pidfile ${pidfile} --chdir ${cur_dir} -w myapp:flask_app -d ${logfile} --logformat "${UWSGI_LOG_FORMAT}"
    fi
    sleep 1
    pid=`get_pid`
    if [ "X$pid" = "X" ];then
        echo "Start uwsgi-${app} failed"
        exit 1
    else
        echo "Start uwsgi-${app} success![$pid]"
    fi
}

function Stop(){
    pid=`get_pid`
    if [ "X$pid" = "X" ];then
        echo "uwsgi-${app} is not running!"
    else
        ${UWSGI} --uid ${USER} --stop ${pidfile}
        if [ $? -ne 0 ];then
            echo "Stop uwsgi-${app} failed![$pid]"
            exit 1
        else
            echo "Stop uwsgi-${app} success!"
        fi
    fi
}

function Reload(){
    pid=`get_pid`
    if [ "X$pid" = "X" ];then
        echo "uwsgi-${app} is not running!"
        Start
    else
        ${UWSGI} --uid ${USER} --reload ${pidfile}
        if [ $? -ne 0 ];then
            echo "Reload uwsgi-${app} failed![$pid]"
            exit 1
        else
            pid=`get_pid`
            if [ "X$pid" != "X" ];then
                echo "Reload uwsgi-${app} success![$pid]"
            else
                echo "Reload uwsgi-${app} failed!"
                exit 1
            fi
        fi
    fi
}


cur_dir="$(cd `dirname "$0"` && pwd)"
UWSGI='/data/apps/py36_flask/bin/uwsgi'
UWSGI_LOG_FORMAT='"%(ltime)" "%(addr)" "%(uagent)" "%(method) %(uri)" %(cl)B %(status) %(rsize)B %(msecs)ms'
USER='uwsgi'

app='web'
host='127.0.0.1'
port='8890'
pidfile="/var/run/uwsgi-${app}.pid"
logfile="/var/log/uwsgi-${app}.log"

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
