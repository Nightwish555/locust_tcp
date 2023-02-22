#!/usr/bin/env python

"""
Locust对TCP长连接进行压力的测试脚本示例。
本脚本通过TCP长连接发送简单的数据
脚本通过记录请求发送的时间，以及成功接收服务器响应数据的时间，计算请求的响应时间。
如果有任何异常抛出，则记录异常信息。
用户可以在脚本中设置一些Locust的参数，如最小等待时间、最大等待时间，以及被测的服务器地址等。
用户可以在此基础上进行扩展，编写适合实际业务场景的测试脚本。
执行脚本：
locust -f locust_tcp.py
"""

import time
import socket
from locust import TaskSet, task, events
from socket.client import Client


class UserBehavior(TaskSet):

    def on_start(self):
        self._key = b""
        self.json_bytes = b""
        self.client.connect()

    def on_stop(self):
        self.client.close()

    def send(self):
        self.client.pack_send(self._key, self.json_bytes)

    def recv(self):
        return self.client.unpack_recv(self._key)

    @task(5)
    def test(self):
        self.send()
        self.recv()


class SocketUser(User):
    # 目标地址
    host = ""
    # 目标端口
    port = 7777
    is_login = 0
    tag = "tag"
    tasks = [UserBehavior]
    wait_time = between(1, 2)

    def __init__(self, *args, **kwargs):
        super(SocketUser, self).__init__(*args, **kwargs)
        self.client = Client(addr=(self.host, self.port), is_login=self.is_login, tag=self.tag)
