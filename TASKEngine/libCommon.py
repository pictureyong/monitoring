#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： 错误信息保存
# 摘    要： 保存定义相关错误信息
# 作    者： lzy<zhengyong.liu@guohead.com>'
# 版    本： 1.0
# 创建日期： 2015-08-10

G_PUT_TTR = 3600
G_RESERVE_TIMEOUT = 10
G_WAIT_RESPONSE_TIME = 60
G_MONITORING_RESPONSE_TUBE = "monitoring_response"

G_COMMON_ERROR      = -1
G_REDIS_ERROR       = 1
G_MYSQL_ERROR       = 2
G_BEANSTALKD_ERROR  = 3
G_WAIT_TIMEOUT      = 4

G_errorID2ErrorMsg = {
    G_COMMON_ERROR      : "common error",
    G_REDIS_ERROR       : "redis error",
    G_MYSQL_ERROR       : "mysql error",
    G_BEANSTALKD_ERROR  : "beanstalkd error",
    G_WAIT_TIMEOUT      : "waiting for the return timeout",
}

# 错误类 m_nErrorID == 0 表示无错误
# m_nErrorID == 1  Redis 错误
# m_nErrorID == 2  mysql 错误
# m_nErrorID == 3  beanstalkd 错误
class CTError:
    def __init__(self, id = 0, msg = ""):
        self.m_nErrorID = id
        self.m_strErrorMsg = msg

    def toDict(self):
        return {"errorID": self.m_nErrorID, "errorMsg": self.m_strErrorMsg}

    def setErrorID(self, id):
        self.m_nErrorID = id

    def setErrorMsg(self, msg):
        self.m_strErrorMsg = msg

    def getErrorID(self):
        return self.m_nErrorID

    def getErrorMsg(self):
        return self.m_strErrorMsg

    def isSuccess(self):
        return 0 == self.m_nErrorID

    def toString(self):
        if self.m_nErrorID != 0 and self.m_strErrorMsg == "":
            self.m_strErrorMsg = G_errorID2ErrorMsg.get(self.m_nErrorID, "")
        return '{"m_nID": %d, "m_strMsg": "%s"}' % (self.m_nErrorID, self.m_strErrorMsg)