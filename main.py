# coding:utf-8
from LogHelper import LogHelper
from MySocket import MySocketServer
from CommonAPI import get_log_name

if __name__ == '__main__':
    mylogger = LogHelper(get_log_name())
    server = MySocketServer(mylogger)
    server.run_forever()
