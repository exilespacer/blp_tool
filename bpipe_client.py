__author__ = 'yen'
import zmq
import time


def realtime_msg_generator(port=5556):
    socket = zmq.Context().socket(zmq.PAIR)
    socket.connect("tcp://192.168.1.110:%s" % port)
    while True:
        msg = socket.recv_pyobj()
        yield msg
        time.sleep(1)

if __name__ == '__main__':
    for msg in realtime_msg_generator():
        print(msg)
