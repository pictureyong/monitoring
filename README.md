需求
一台服务器控制多台服务器执行 shell 命令并显示执行结果

功能
支持多台机器的同步执行和异步执行 设置超时时间
支持服务分组选择执行

实现
使用 beanstalkc 消息队列 使用 socket.gethostname() 作为被控主机的消息管道名 控制主机将消息发送到被控主机的消息管道 被控主机执行相应 shell 命令 并返回执行结果

部署
monitoring-server.py 部署并在每台被控主机上执行
python monitoring-server.py                         -- 运行脚本的用户的权限决定了控制机在该台被控机上执行 shell 命令的权限
python monitoring-run.py help                       -- 获取执行帮助
python monitoring-run.py 'df -lh' DF_LH 60 ASYNC    -- 控制机上执行  DF_LH 是 common.py 里 G_SERVER_HOST_NAME 的主机分组名