# coding:utf-8
from LogHelper import LogHelper
from MySocket import MySocketServer
from CommonAPI import get_log_name
from ModbusProtocol import ModbusType
import gevent
from gevent import monkey
monkey.patch_all()

if __name__ == '__main__':
    # br = bytearray(b'\x00\x01'*10)
    # print(br)
    # exit(0)
    mylogger = LogHelper(get_log_name())
    mobusinfo = ModbusType(mylogger)
    server = MySocketServer(mylogger, mobusinfo)
    gevent.spawn(server.run_forever())
