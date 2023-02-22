import os
import struct
import json
import socket

from google.protobuf import json_format
from protobuf.down_pb2 import down_msg
from protobuf.up_pb2 import up_msg
from utils.tool import encrypt, decrypt, record_result
from loguru import logger
from locust import events


class Client:
    socket_dict = {
        0: "链接成功", -1: "链接失败", 13: "连接广播地址或由于防火墙策略失败", 11: "没有足够空闲的本地端口",
        110: "ETIMEDOUT",
        115: "套接字为非阻塞套接字，且连接请求没有立即完成",
        111: "远程地址并没有处于监听状态", 4: "系统调用的执行由于捕获中断而中止"
    }
    # 加密key
    key = b""

    def __init__(self, addr: tuple, is_login: int, tag: str):
        self.client = None
        self.addr = addr
        self.device_id = "121#25997"
        self.is_login = is_login
        self.tag = tag
        self.packet_detection = bool

    def connect(self):
        """
        登录
        """
        start_time = time.time()
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn_result = self.client.connect_ex(self.addr)
            logger.info(self.socket_dict.get(conn_result))
        except socket.gaierror as e:
            logger.exception(f"服务器链接失败 堆栈:{e}")
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="connect", name="connect", response_time=total_time,
                                        response_length=0, exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="connect", name="connect", response_time=total_time,
                                        response_length=0)

    def pack_send(self, _key: bytes, json_bytes: bytes):
        """
        发包
        :param _key: 加密key
        :param json_bytes: protobuf 加密后的数据
        :return:
        """
        # 加密数据
        start_time = time.time()
        try:
            encrypt_data = encrypt(_key, json_bytes)
            # 包体
            device_id_byte_size = len(self.device_id)
            # 大小端 自行定义
            head_bytes = struct.pack("", self.is_login, device_id_byte_size)
            body = head_bytes + self.device_id.encode() + encrypt_data

            # 发送的 数据包
            body_size = len(body)
            data_pack = struct.pack("", body_size) + body
            self.client.send(data_pack)
        except Exception as e:
            logger.error(f"{self.tag} 发包出现错误 堆栈:{e}")
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="send", name="send", response_time=total_time, response_length=0,
                                        exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="send", name="send", response_time=total_time, response_length=0)

    def unpack_recv(self, _key: bytes):
        """收包 解包"""
        global backpack_data
        start_time = time.time()
        try:
            packet = self.client.recv(4)
            if not packet:
                logger.error(f"{self.tag} 没有收到包头 ")
                total_time = int((time.time() - start_time) * 1000)
                events.request_failure.fire(request_type="recv_eio", name="recv_eio", response_time=total_time,
                                            response_length=0, exception=packet)
                return False
            else:
                logger.info(f"{self.tag} 收到包头 device_id: {self.device_id}")
            head_len = struct.unpack("", packet)[0]

            packet = self.client.recv(head_len)
            while len(packet) < head_len:
                packet += self.client.recv(head_len - len(packet))
            dec_data = decrypt(_key, packet)
            len_body = struct.unpack("<i", dec_data[:4])[0]
            backpack_data = dec_data[4:len_body + 4]
            logger.info(f"{self.tag} 收到回包")

        except IOError as e:
            logger.exception(f"{self.tag} 收包出现错误 堆栈: {e}")
            total_time = int((time.time() - start_time) * 1000)
            if e.errno == errno.EPIPE:
                events.request_failure.fire(request_type="recv_epipe", name="recv_epipe", response_time=total_time,
                                            response_length=0, exception=e)
            else:
                events.request_failure.fire(request_type="recv_eio", name="recv_eio", response_time=total_time,
                                            response_length=0, exception=e)

        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="recv", name="recv", response_time=total_time, response_length=0,
                                        exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="recv", name="recv", response_time=total_time, response_length=0)
        return backpack_data

    def close(self):
        """socket 关闭"""
        self.client.close()
