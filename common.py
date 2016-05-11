#!/usr/bin/env python
# -*- coding: utf8 -*-

# Copyright (c) 2015, 果和
# All rights reserved.
# 名    称： 监控脚本公共函数
# 摘    要： 监控脚本中所使用的公共函数只定义一遍
# 作    者： lzy<zhengyong.liu@guohead.com>'
# 版    本： 1.0
# 创建日期： 2015-05-19

import time
import datetime
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE,formatdate

G_SERVER_HOST_NAME = {
    "ALL": [],
    "SLOW_LOG" : ["db2", "vm55", "vm63", "vm85", "vm93", "vm95", "w2" ],
    "DF_LH" : ["db1", "db2", "db3", "db4", "c2"],
}

G_DF_LH_PERC_LIMIT = 80
G_SLOW_NUM_LIMIT = 150000

# 预警级别
G_LEVEL_RIGHT = 0
G_LEVEL_LITTLE = 1
G_LEVEL_WARN = 2
G_LEVEL_SERIOUSE = 3
G_DIT_LEVEL = {
    G_LEVEL_RIGHT : "正确",
    G_LEVEL_LITTLE : "可忽略",
    G_LEVEL_WARN : "警告",
    G_LEVEL_SERIOUSE : "严重",
}

getLevel = lambda x, y : x if x > y else y

# 预警邮件接收则列表
G_REC_MAIL_ADDRESS = ["zhengyong.liu@guohead.com"]
G_REC_MAIL_ENGINEER_ADDRESS = ["zhengyong.liu@guohead.com"]

todayZeroTime = lambda : time.mktime(datetime.date.today().timetuple())

trans = lambda s: s.encode("utf8") if isinstance(s, unicode) else str(s)


# 使用 STMTP 发送邮件
# The arguments are:
# to 收件邮箱列表                   ["zhengyong.liu@guohead.com", "pictureyong@163.com"]
# subject 邮件主题                  string
# text 邮件正文                     string
# serviceConfig 发件邮箱服务配置    { "user": "", "passwd": "", "serverName": "smtp.126.com", }
def sendMail(to, subject, text, serviceConfig):
    msg = MIMEMultipart()
    msg["From"] = serviceConfig["user"]
    msg["Subject"] = subject
    msg["To"] = COMMASPACE.join(to)
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(text, _charset="gbk"))
    smtp = smtplib.SMTP(serviceConfig["serverName"])
    smtp.login(serviceConfig["user"], serviceConfig["passwd"])
    smtp.sendmail(serviceConfig["user"], to, msg.as_string())
    smtp.close()