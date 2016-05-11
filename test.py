#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： 测试用例
# 摘    要： 测试提供的各个接口是否正常运行
# 作    者： lzy<zhengyong.liu@guohead.com>'
# 版    本： 1.0
# 创建日期： 2015-08-10

import commands
from TASKEngine.TaskEngine import CTaskEngine

def getPid(process):
    cmd = "ps aux | grep '%s' | grep -v 'grep' " % (process)
    info = commands.getoutput(cmd)
    infos = info.split()
    if len(infos) > 1:
        return infos[1]
    else:
        return -1

queueConfig = {
    'host': '10.5.4.171',
    'port': 11300,
    'parse_yaml': False
}

loggerConfig = {
    "loggerPaht" : "E:\\DATA\\log\\test.log"
}

serverTube = "TEST_TEST_A"

def testA():
    engine = CTaskEngine(queueConfig, loggerConfig, serverTube)
    engine.init()
    engine.start()
    taskHandle = engine.getHandleApi()
    error, answer = taskHandle.execute_sync("Master.Hadoop", "df -lh")
    print "**********************************"
    print error.toString()
    for key, value in answer.iteritems():
        print key, value
    print "**********************************"
    engine.joinAll()

def onExecute(answer, error):
    print "onExecute"
    print error.toString()
    print answer

def testB():
    engine = CTaskEngine(queueConfig, loggerConfig, serverTube)
    engine.init()
    engine.start()
    taskHandle = engine.getHandleApi()
    func = taskHandle.execute_async("Master.Hadoop", "df -lh", onExecute, 10)
    if func:
        print "FUNCCCC"
        func()
    engine.joinAll()
    print "abcd"

if "__main__" == __name__:
    print "START"
    #for i in xrange(1, 10):
    testA()
    print "OVER"
