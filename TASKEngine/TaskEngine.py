#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： TaskEngine
# 摘    要： 对外提供启动 和 获得对象接口
# 作    者： lzy<zhengyong.liu@guohead.com>'
# 版    本： 1.0
# 创建日期： 2015-08-10

import logging
import libCommon

from TaskHandle import CTaskHandle

class CTaskEngine:
    def __init__(self, queueConfig, loggerConfig, serverTube = None, litTubeName = [], cmdNum = 1):
        self.m_queueConfig = queueConfig
        self.m_loggerConfig = loggerConfig
        if serverTube:
            self.m_serverTube = serverTube
        else:
            self.m_serverTube = libCommon.G_MONITORING_RESPONSE_TUBE
        self.m_litTubeName = litTubeName
        self.m_nCmdNum = cmdNum

    def init(self):
        self.m_logger = logging.getLogger(self.m_loggerConfig.get("loggerName", "TaskEngine"))
        self.m_logger.setLevel(self.m_loggerConfig.get("loggerLevel", logging.INFO))
        handlerA = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s|%(levelname)s|%(lineno)d|%(message)s")
        handlerA.setFormatter(formatter)
        handlerB = logging.FileHandler(self.m_loggerConfig.get("loggerPaht", "/data/log/crontab/TaskEngine.log"))
        handlerB.setFormatter(formatter)
        self.m_logger.addHandler(handlerA)
        self.m_logger.addHandler(handlerB)
        self.m_taskHandle = CTaskHandle(self.m_queueConfig, self.m_litTubeName, self.m_logger, self.m_nCmdNum, self.m_serverTube)

    def getHandleApi(self):
        return self.m_taskHandle

    def start(self):
        self.m_logger.info("--- SERVER START ---")
        self.m_taskHandle.startAll()

    def joinAll(self):
        self.m_taskHandle.joinAll()