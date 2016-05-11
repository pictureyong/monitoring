#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： 实现类似 boost 库的 deadline_timer 类
# 摘    要： 异步定时函数调用
# 作    者： lzy<zhengyong.liu@guohead.com>
# 版    本： 1.0
# 创建日期： 2015-08-13

import time
import threading

from threading import RLock
from libCommon import CTError

class CDeadlineTimer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.m_nExpiryTime = 0
        self.m_nStartTime = time.time()
        self.m_lock = RLock()
        self.m_bIsCancel = False
        self.m_bIsWating = True

    def run(self):
        endTime = self.m_nStartTime + self.m_nExpiryTime
        while time.time() < endTime:
            time.sleep(1)
            if self.m_lock.acquire():
                if self.m_bIsCancel:
                    self.m_lock.release()
                    break
                else:
                    self.m_lock.release()
        if self.m_lock.acquire():
            self.m_bIsWating = False
            if self.m_bIsCancel:
                return self.m_lock.release()
            self.m_lock.release()
            self.runCallBack()

    def expires_from_now(self, expiry_time):
        self.m_nExpiryTime = expiry_time
        self.m_nStartTime = time.time()

    def async_wait(self, func, *arg):
        self.m_callBack = func
        self.m_arg = arg

    def cancelWait(self):
        if self.m_lock.acquire():
            self.m_bIsCancel = True
            if self.m_bIsWating:
                return CTError(), self.m_lock.release()
            else:
                return CTError(-1, "callBack is already running"), self.m_lock.release()

    def runCallBack(self):
        self.m_callBack(*self.m_arg)