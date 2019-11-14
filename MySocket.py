from LogHelper import LogHelper
import socket
from CommonAPI import disp_binary
from ModbusProtocol import ModbusType
from BasicConfig import SocketConfig
import traceback
import time
import gevent
from gevent import monkey

monkey.patch_all()


class MySocketServer:
    def __init__(self, mylog: LogHelper, modbus: ModbusType, addr: tuple = SocketConfig.server_addr,
                 buff: int = SocketConfig.recv_buff,
                 listen_num=SocketConfig.lister_num):
        self.server_addr = addr
        self.log: LogHelper = mylog
        self.recv_buff = buff
        self.listen_num = listen_num
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.client_addr = None
        self.mobus_info = modbus
        self.socket_server.bind(self.server_addr)
        self.socket_server.listen(self.listen_num)
        self.log.warn("server_addr:{} listen_port:{}".format(self.server_addr[0], self.server_addr[1]))

    def run_forever(self):
        while True:
            try:
                # self.conn, self.client_addr = self.socket_server.accept()
                conn, client_addr = self.socket_server.accept()
                self.log.warn('got connected from{}'.format(client_addr))
                gevent.spawn(self.process_msg, conn, client_addr)
            except Exception:
                self.log.error(traceback.format_exc())
                self.log.error('sleep 10s and retry...')
                time.sleep(10)

    def process_msg(self,conn, client_addr):
        while True:
            try:
                ra = conn.recv(self.recv_buff)
                self.log.info('{} recv len:{}'.format(client_addr, len(ra)))
                if len(ra) <= 0:
                    # self.log.warn("receive 0 bytes msg!")
                    # continue
                    self.log.warn("try to close connection for receive 0 bytes msg")
                    conn.close()
                    self.log.warn("close connection for receive 0 bytes msg complete")
                    break
                if self.mobus_info:
                    self.mobus_info.recv_new_msg(ra)
                else:
                    self.mobus_info = ModbusType(self.log, ra)
                if not self.mobus_info.recv_valid:
                    continue
                self.mobus_info.handle_reply_msg()
                if self.mobus_info.send_data_bytes:
                    self.log.info("{} send:{}".format(client_addr, disp_binary(self.mobus_info.send_data_bytes)))
                    conn.send(self.mobus_info.send_data_bytes)
            except:
                self.log.error(traceback.format_exc())
                raise
