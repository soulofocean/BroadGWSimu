# coding:utf-8
import socket
import time

if __name__ =='__main__':
    sock = socket.socket()
    sock.connect(('172.26.92.152', 502))
    sock.send(b"\x00\x01\x02\x03")
    print("sent",b'\x00\x01\x02\x03')
    sock.send(b"")
    # print("sent", b'')
    print('wait 3s')
    time.sleep(3)
    print('try to close')
    sock.close()
    print('close complete')