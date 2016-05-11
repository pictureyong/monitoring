#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： beanstalkd 任务发送接收
# 摘    要： job 命令发送到 beanstalkd 任务队列中，接收任务队列的反馈
# 作    者： lzy<zhengyong.liu@guohead.com>'
# 版    本： 1.0
# 创建日期： 2015-08-10

import threading
import beanstalkc
import libCommon
import time

from libCommon import CTError

class CTaskTransport(threading.Thread):
    def __init__(self, queueConfig, litTubeName, logger, taskHandle, cmdNum, tubeName):
        threading.Thread.__init__(self)
        self.m_nCmdNum = cmdNum
        try:
            self.m_queueConfig = queueConfig
            self.m_logger = logger
            self.m_taskHandle = taskHandle
            self.m_receiveBq = beanstalkc.Connection(**queueConfig)
            self.m_receiveBq.watch(tubeName)
            self.m_receiveBq.ignore("default")
            self.m_sendBq = dict((k, beanstalkc.Connection(**queueConfig)) for k in litTubeName)
            for tube, queue in self.m_sendBq.iteritems():
                queue.use(tube)
        except Exception, ex:
            self.m_logger.error("init beanstalk connect error, errorMsg: %s" % str(ex))
            exit(1)

    def run(self):
        self.receiveJob()
        return

    def putJob(self, tubeName, jobBody):
        tError = CTError()
        if self.m_sendBq.has_key(tubeName) == False:
            self.m_sendBq[tubeName] = beanstalkc.Connection(**self.m_queueConfig)
            self.m_sendBq[tubeName].use(tubeName)
        try:
            self.m_sendBq[tubeName].put(jobBody, libCommon.G_PUT_TTR)
        except Exception, ex:
            tError.setErrorID(libCommon.G_BEANSTALKD_ERROR)
            tError.setErrorMsg(str(ex))
        return tError

    def receiveJob(self):
        while self.m_nCmdNum > 0:
            try:
                job = self.m_receiveBq.reserve(libCommon.G_RESERVE_TIMEOUT)
                if job:
                    self.m_taskHandle.doBeanstalkdJob(job)
            except Exception, ex:
                self.m_logger.error("Error when processing received job, %s" % str(ex))
                time.sleep(10)
            finally:
                if job:
                    job.delete()
        return

    def subOneCmdNum(self):
        self.m_nCmdNum -= 1

    def deleteJobByID(self, tube, jobID):
        if self.m_sendBq.has_key(tube):
            self.m_sendBq[tube].delete(jobID)
        return