from LogHelper import LogHelper
import socket
from CommonAPI import disp_binary
from ModbusProtocol import ModbusType
from BasicConfig import SocketConfig
import traceback

class MySocketServer:
    def __init__(self, mylog: LogHelper, addr: tuple = SocketConfig.server_addr, buff: int = SocketConfig.recv_buff,
                 listen_num=SocketConfig.lister_num):
        self.server_addr = addr
        self.log: LogHelper = mylog
        self.recv_buff = buff
        self.listen_num = listen_num
        self.socket_server = None
        self.conn = None
        self.client_addr = None

    def run_forever(self):
        while True:
            try:
                self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_server.bind(self.server_addr)
                self.socket_server.listen(self.listen_num)
                self.log.warn("server_addr:{} listen_port:{}".format(self.server_addr[0], self.server_addr[1]))
                self.conn, self.client_addr = self.socket_server.accept()
                self.log.warn('got connected from{}'.format(self.client_addr))
                while True:
                    ra = self.conn.recv(self.recv_buff)
                    self.log.info('recv len:{}'.format(len(ra)))
                    if len(ra) <= 0:
                        self.log.warn("try to close connection for receive 0 bytes msg")
                        self.conn.close()
                        self.log.warn("close connection for receive 0 bytes msg complete")
                        break
                    resv_info = ModbusType(self.log, ra)
                    if not resv_info.recv_valid:
                        continue
                    resv_info.handle_reply_msg()
                    if resv_info.send_data_bytes:
                        self.log.info("send:{}".format(disp_binary(resv_info.send_data_bytes)))
                        self.conn.send(resv_info.send_data_bytes)
            except Exception:
                self.log.error(traceback.format_exc())
