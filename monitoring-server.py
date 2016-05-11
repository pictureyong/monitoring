#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： 监控服务器
# 摘    要： 该脚步运行于所有有监控需求的服务器, 接收 beanstalkd 里的 job 已 shell 方式运行, 并将运行结果写回 beanstalkd
# 作    者： lzy<zhengyong.liu@guohead.com>"
# 版    本： 1.0
# 创建日期： 2015-08-06

import os
import json
import beanstalkc
import socket
import threading
import msgpack
import daemonize
import logging
import time

from config import BASECONF
from threading import RLock

G_MONITORING_RESPONSE_TUBE = "monitoriong_response"
APP = "monitoring-server"
G_RESERVE_TIME_OUT = 600
CURR_DIR = os.path.abspath('./')

queueConfig = BASECONF['QUEUE_PARAMS']

class CClearBeanstalkd(threading.Thread):
    def __init__(self, queueConfig, logger):
        threading.Thread.__init__(self)
        self.m_queueConfig = queueConfig
        self.m_logger = logger
        self.m_deleteTimeOut = 600
        self.m_qb = None
        self.m_litTube = []
        self.m_lock = RLock()

    def getBeanstalkdConnect(self):
        try:
            if self.m_qb:
                self.m_qb.close()
            qb = beanstalkc.Connection(**self.m_queueConfig)
        except Exception, ex:
            self.m_logger.error("beanstalk connection error, %s" % str(ex))
        return qb

    # '---\n- TEST\n- ABC\n- BCD\n- BCD-\n'
    def onlyWatch(self, tube):
        curWatching = self.m_qb.watching()
        lit = curWatching.split("\n")
        litWatching = []
        for value in lit:
            value = value.lstrip("- ")
            if value:
                litWatching.append(value)
        if tube not in litWatching:
            self.m_qb.watch(tube)
        for value in litWatching:
            if value != tube:
                self.m_qb.ignore(value)
        return

    def run(self):
        self.m_qb = self.getBeanstalkdConnect()
        while True:
            curTime = time.time()
            if self.m_lock.acquire():
                cout = 0
                for putTime, jobID in self.m_litTube:
                    if curTime - putTime > self.m_deleteTimeOut:
                        if self.deleteJob(jobID):
                            cout += 1
                        else:
                            break
                    else:
                        break
                del self.m_litTube[:cout]
                self.m_lock.release()
            time.sleep(10)

    def deleteJob(self, jobID):
        try:
            if self.m_qb.peek(jobID):
                self.m_qb.delete(jobID)
            return True
        except Exception, ex:
            self.m_logger.error("Error when processing received job, Exception: %s" % str(ex))
            time.sleep(10)
            self.m_qb = self.getBeanstalkdConnect()
        return False

    def addJobID(self, jobID, putTime):
        if self.m_lock.acquire():
            self.m_litTube.append(([putTime, jobID]))
            self.m_lock.release()

class CCMDRunServer:
    def __init__(self, queueConfig, tube, logger):
        self.m_queueConfig = queueConfig
        self.m_strTube = tube
        self.m_logger = logger
        self.m_qb = None
        self.m_clearBeanstalkd = CClearBeanstalkd(queueConfig, logger)

    def initBeanstalkdConnection(self):
        self.m_logger.info("initBeanstalkdConnection")
        try:
            if self.m_qb:
                self.m_qb.close()
            self.m_qb = beanstalkc.Connection(**self.m_queueConfig)
            self.m_qb.watch(self.m_strTube)
            self.m_qb.ignore("default")
            self.m_qb.use(G_MONITORING_RESPONSE_TUBE)
        except Exception, ex:
            self.m_logger.error("connect beanstalkd except, Exception: %s" % str(ex))

    def run(self):
        self.m_clearBeanstalkd.start()
        self.initBeanstalkdConnection()
        while True:
            try:
                job = self.m_qb.reserve(G_RESERVE_TIME_OUT)
                if not job:
                    continue
                data = msgpack.unpackb(job.body)
                self.m_logger.info(json.dumps(data))
                cmd = data.get("PARAM")
                tube = data.get("TUBE", G_MONITORING_RESPONSE_TUBE)
                excet = os.popen(cmd)
                data.update({"PARAM": excet.read()})
                self.m_qb.use(tube)
                try:
                    jobID = self.m_qb.put(msgpack.packb(data))
                    self.m_clearBeanstalkd.addJobID(jobID, time.time())
                except Exception, ex:
                    self.m_logger.error("Error when processing put job, Exception: %s" % str(ex))
                finally:
                    job.delete()
            except Exception, ex:
                self.m_logger.error("Error when processing received job, Exception: %s" % str(ex))
                time.sleep(10)
                self.initBeanstalkdConnection()
        return

def main():
    logger = logging.getLogger(__name__)
    logger.info("[%s] start" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
    hostName = socket.gethostname()
    server = CCMDRunServer(queueConfig, hostName, logger)
    server.run()

if "__main__" == __name__:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("/data/log/crontab/monitoring-server.log", "ab")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s|%(levelname)s|%(lineno)d|%(message)s"))
    logger.addHandler(fh)
    keep_fds = [fh.stream.fileno()]
    daemon = daemonize.Daemonize(app=APP, pid="%s/monitoring-server.pid" % CURR_DIR, action=main, keep_fds=keep_fds)
    daemon.start()