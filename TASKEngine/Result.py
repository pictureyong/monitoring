#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： 结果封装
# 摘    要： 回调函数和结果的封装
# 作    者： lzy<zhengyong.liu@guohead.com>'
# 版    本： 1.0
# 创建日期： 2015-08-10

import libCommon

from threading import Condition
from libCommon import CTError
from deadlineTimer import CDeadlineTimer

class CResult:
    def __init__(self, callBack, taskHandle, seq, isSync = False, timeOut = 60):
        self.m_callBack = callBack
        self.m_taskHandle = taskHandle
        self.m_nSeq = seq
        self.m_isSync = isSync
        self.m_condition = Condition()
        self.m_nTimeOut = timeOut
        self.m_bIsGetAnswer = False
        self.m_bIsWait = False
        self.m_error = CTError()
        self.m_answer = {}
        self.m_timer = None

    def takeAnswer(self):
        #self.m_lock.acquire()
        return self.m_error, self.m_answer, None#self.m_lock.release()

    def giveAnswer(self, answer, isError):
        if self.m_condition.acquire():
            if self.m_bIsGetAnswer == False:
                self.m_bIsGetAnswer = True
                if isError:
                    self.m_error.setErrorID(answer.get("errorID", libCommon.G_COMMON_ERROR))
                    self.m_error.setErrorMsg(answer.get("errorMsg", ""))
                else:
                    self.m_answer.update(answer)
                if self.m_isSync:
                    if self.m_bIsWait:
                        self.m_condition.notify()
                else:
                    if self.m_error.getErrorID() != libCommon.G_WAIT_TIMEOUT:
                        self.killTimer()
                    self.notify(self.m_answer, self.m_error)
            self.m_condition.release()
            self.m_taskHandle.removeSeq(self.m_nSeq)
        return

    def startTimer(self):
        self.m_timer = CDeadlineTimer()
        self.m_timer.expires_from_now(self.m_nTimeOut)
        self.m_timer.async_wait(self.onTimer)
        return self.m_timer.start

    def joinAll(self):
        if self.m_timer:
            try:
                self.m_timer.join()
            except Exception, ex:
                pass

    def onTimer(self):
        self.giveAnswer({"errorID": libCommon.G_WAIT_TIMEOUT}, True)
        self.m_timer = None

    def killTimer(self):
        if self.m_timer:
            error = self.m_timer.cancelWait()
            # if error.isSuccess() == False:
            #     self.m_logger.error("killTimer error, %s" % error.toString())

    def waitForComplete(self):
        if self.m_condition.acquire():
            if self.m_bIsGetAnswer == False:
                self.m_bIsWait = True
                self.m_condition.wait(self.m_nTimeOut)
                if self.m_bIsGetAnswer == False:
                    self.m_bIsGetAnswer = True
                    self.m_error.setErrorID(libCommon.G_WAIT_TIMEOUT)
                    self.m_taskHandle.removeSeq(self.m_nSeq)
            self.m_condition.release()

    def notify(self, answer, error):
        if self.m_callBack:
            self.m_callBack(answer, error)