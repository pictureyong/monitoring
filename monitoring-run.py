#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： 监控服务器调用者
# 摘    要： 主要监控服务慢日志  服务硬盘占用
# 作    者： lzy<zhengyong.liu@guohead.com>"
# 版    本： 1.0
# 创建日期： 2015-08-06

import sys
import time
import socket
import re
import common
import commands

from TASKEngine.TaskEngine import CTaskEngine
from common import sendMail
from config import BASECONF

G_DEFAULT_TIME_OUT = 600

G_APP = "monitoring-run.py"
G_LOGGER_CONFIG = {
    "loggerPaht" : "/data/log/crontab/monitoring-run.log"
}

'''
一  月：January    简写:Jan.
二  月：February   简写:Feb.
三  月：March      简写:Mar.
四  月：April      简写:Apr.
五  月：May        简写:May.
六  月：June       简写:Jun.
七  月：July       简写:Jul.
八  月：August     简写:Aug.
九  月：September  简写:Sep.
十  月：October    简写:Oct.
十一月：November   简写:Nov.
十二月：December   简写:Dec.
'''
G_ditMonth = {
    "01": "Jan",
    "02": "Feb",
    "03": "Mar",
    "04": "Apr",
    "05": "May",
    "06": "Jun",
    "07": "Jul",
    "08": "Aug",
    "09": "Sep",
    "10": "Oct",
    "11": "Nov",
    "12": "Dec",
}

def getPid(process):
    cmd = "ps aux | grep '%s' | grep -v 'grep' " % (process)
    info = commands.getoutput(cmd)
    infos = info.split()
    if len(infos) > 1:
        return infos[1]
    else:
        return -1

def getServerTube():
    date = time.strftime("%Y-%m-%d")
    hostName = socket.gethostname()
    pid = getPid(G_APP)
    return "%s_%s_%s" % (date, hostName, str(pid))

def checkSlowLog(taskHandle, litHost, date):
    mailSubject = "API 慢日志监控 CHECK_TIME: %s" % (time.strftime("%Y%m%d-%H:%M:%S"))
    retMsg = ""
    infoMsg = ""
    lit = date.split("-")
    strg = lit[2] + "-" + G_ditMonth.get(lit[1]) + "-" + lit[0]
    cmd = "cat /var/log/slow.php.file.log | grep '^\[%s' | wc -l" % strg
    taskHandle.logInfo("\n"+cmd)
    slowNum = 0
    for host in litHost:
        error, answer = taskHandle.execute_sync(host, cmd, G_DEFAULT_TIME_OUT)
        if error.isSuccess():
            taskHandle.logInfo("\nhost: %s\n%s" % (host, answer["RET"]))
            slowNum += int(answer["RET"])
            infoMsg += "%s: %d\n" % (host, int(answer["RET"]))
        else:
            retMsg += host + ": " + error.toString() + "\n"
    taskHandle.logInfo("Total slowNum: %d" % slowNum)
    if slowNum > common.G_SLOW_NUM_LIMIT:
        retMsg += "date: %s, slowNum: %d > %d\n" % (date, slowNum, common.G_SLOW_NUM_LIMIT)
    if retMsg:
        taskHandle.logInfo(retMsg)
        retMsg += "\n" + infoMsg
        sendMail(common.G_REC_MAIL_ENGINEER_ADDRESS, mailSubject, retMsg, BASECONF["FROM_MAIL_SERVIVE"])

def checkDf(taskHandle, litHost):
    mailSubject = "服务器硬盘占用比例检测 CHECK_TIME: %s" % (time.strftime("%Y%m%d-%H:%M:%S"))
    retMsg = ""
    reObj = re.compile("(\d+)%")
    cmd = "df -lh"
    taskHandle.logInfo("\n"+cmd)
    for host in litHost:
        error, answer = taskHandle.execute_sync(host, cmd)
        if error.isSuccess():
            taskHandle.logInfo("\nhost: %s\n%s" % (host, answer["RET"]))
            runMsg = answer["RET"]
            lit = runMsg.split("\n")
            for line in lit:
                lit = reObj.findall(line)
                if lit:
                    perc = int(lit[0])
                    if perc > common.G_DF_LH_PERC_LIMIT:
                        retMsg += "host: %s, %d > %d, %s\n" % (host, perc, common.G_DF_LH_PERC_LIMIT, line)
        else:
            retMsg += host + ": " + error.toString() + "\n"
    if retMsg:
        taskHandle.logInfo(retMsg)
        sendMail(common.G_REC_MAIL_ENGINEER_ADDRESS, mailSubject, retMsg, BASECONF["FROM_MAIL_SERVIVE"])

def getTaskHandle(reqNum):
    engine = CTaskEngine(BASECONF["QUEUE_PARAMS"], G_LOGGER_CONFIG, getServerTube(), [], reqNum)
    engine.init()
    engine.start()
    taskHandle = engine.getHandleApi()
    return taskHandle

def checkAll():
    taskHandle = getTaskHandle(len(common.G_SERVER_HOST_NAME["DF_LH"]) + len(common.G_SERVER_HOST_NAME["SLOW_LOG"]))
    checkDf(taskHandle, common.G_SERVER_HOST_NAME["DF_LH"])
    date = time.strftime("%Y-%m-%d", time.localtime(time.time() - common.G_ONE_DAY_SECOND))
    checkSlowLog(taskHandle, common.G_SERVER_HOST_NAME["SLOW_LOG"], date)

def runCMD_sync(litHost, cmd, timeOut):
    taskHandle = getTaskHandle(len(litHost))
    taskHandle.logInfo("\n"+cmd)
    for host in litHost:
        error, answer = taskHandle.execute_sync(host, cmd, timeOut)
        if error.isSuccess():
            taskHandle.logInfo("\nhost: %s\n%s" % (host, answer["RET"]))
        else:
            taskHandle.logInfo("\nhost: %s\nexecute fail: %s" % (host, error.toString()))

class CCallback:
    def __init__(self, taskHandle, host):
        self.m_taskHandle = taskHandle
        self.m_strHost = host

    def func(self, answer, error):
        if error.isSuccess():
            self.m_taskHandle.logInfo("\nhost: %s\n%s" % (self.m_strHost, answer["RET"]))
        else:
            self.m_taskHandle.logInfo("\nhost: %s\nexecute fail: %s" % (self.m_strHost, error.toString()))

def runCMD_async(litHost, cmd, timeOut):
    taskHandle = getTaskHandle(len(litHost))
    taskHandle.logInfo("\n"+cmd)
    for host in litHost:
        callback = CCallback(taskHandle, host)
        func = taskHandle.execute_async(host, cmd, callback.func, timeOut)
        if func:
            func()

def printGroupInfo():
    print "------- group info -------\n"
    for key, value in common.G_SERVER_HOST_NAME.iteritems():
        print key + "\n" + ", ".join(value)
    print "--------------------------\n"

def main():
    if len(sys.argv) == 1:
        checkAll()
    elif len(sys.argv) == 2:
        if sys.argv[1].upper() == "HELP":
            print '''
env=RUNTIME python monitoring-run.py cmd group timeOut runType
timeOut INT         default 600 second
runType ASYNC/SYNC  default SYNC
*** If there is a default value, it's nullable
example:
    env=RUNTIME python monitoring-run.py "df -lh" DF_LH 10
            '''
            printGroupInfo()
    elif len(sys.argv) >= 3:
        cmd = sys.argv[1]
        group = sys.argv[2]
        timeOut = G_DEFAULT_TIME_OUT
        if len(sys.argv) > 3:
            timeOut = int(sys.argv[3])
        if common.G_SERVER_HOST_NAME.has_key(group):
            if len(sys.argv) == 5 and sys.argv[4].upper() == "ASYNC":
                runCMD_async(common.G_SERVER_HOST_NAME[group], cmd, timeOut)
            else:
                runCMD_sync(common.G_SERVER_HOST_NAME[group], cmd, timeOut)
        else:
            print "can not group, %s" % group
            print printGroupInfo()

if "__main__" == __name__:
    print "******** START ********"
    main()
    print "******** OVER  ********"