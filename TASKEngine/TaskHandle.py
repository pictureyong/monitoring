#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： beanstalkd 任务处理
# 摘    要： 将 CMD 命令打包成 job 交给 TaskTransport 处理, 从 TaskTransport 接收 job 并解析调用相应回调
# 作    者： lzy<zhengyong.liu@guohead.com>'
# 版    本： 1.0
# 创建日期： 2015-08-10

import msgpack

from threading import RLock
from Result import CResult
from TaskTransport import CTaskTransport
from libCommon import G_WAIT_RESPONSE_TIME

class CTaskHandle:
    def __init__(self, queueConfig, litTubeName, logger, cmdNum, serverTube):
        self.m_taskTransport = CTaskTransport(queueConfig, litTubeName, logger, self, cmdNum, serverTube)
        self.m_logger = logger
        self.m_serverTube = serverTube
        self.m_lock = RLock()
        self.m_nSeq = 0
        self.m_seq2Result = {}

    def logInfo(self, msg):
        self.m_logger.info(msg)

    def logError(self, msg):
        self.m_logger.error(msg)

    def startAll(self):
        self.m_taskTransport.start()

    def joinAll(self):
        self.m_taskTransport.join()

    # 异步执行命令
    def execute_async(self, tube, param, callBack, timeOut = G_WAIT_RESPONSE_TIME):
        if callBack:
            if self.m_lock.acquire():
                result = CResult(callBack, self, self.m_nSeq, False, timeOut)
                self.m_seq2Result[self.m_nSeq] = result
                param = self.genParam(self.m_nSeq, param)
                func = result.startTimer()
                error = self.m_taskTransport.putJob(tube, msgpack.packb(param))
                self.m_nSeq += 1
                self.m_lock.release()
                if error.isSuccess() == False:
                    result.giveAnswer(error.toDict(), True)
                return func

    # 同步执行命令
    def execute_sync(self, tube, param, timeOut = G_WAIT_RESPONSE_TIME):
        if self.m_lock.acquire():
            result = CResult(None, self, self.m_nSeq, True, timeOut)
            self.m_seq2Result[self.m_nSeq] = result
            self.m_lock.release()
            param = self.genParam(self.m_nSeq, param)
            self.m_nSeq += 1
            error = self.m_taskTransport.putJob(tube, msgpack.packb(param))
            answer = {}
            if error.isSuccess():
                result.waitForComplete()
                error, answer, _a = result.takeAnswer()
            return error, answer

    def doBeanstalkdJob(self, job):
        data = msgpack.unpackb(job.body)
        seq = data.get("SEQ")
        if seq != None:
            if self.m_lock.acquire():
                result = self.m_seq2Result.get(seq)
                if result:
                    result.giveAnswer({"RET": data.get("PARAM", {})}, False)
                self.m_lock.release()
        return

    def genParam(self, seq, param):
        return {"SEQ": seq, "PARAM": param, "TUBE": self.m_serverTube}

    def getTaskTransport(self):
        return self.m_taskTransport

    def removeSeq(self, seq):
        if self.m_lock.acquire():
            if self.m_seq2Result.has_key(seq):
                self.m_seq2Result[seq].joinAll()
                del self.m_seq2Result[seq]
            self.m_lock.release()
            self.m_taskTransport.subOneCmdNum()
        return
