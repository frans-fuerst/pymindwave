#!/usr/bin/env python3

import mindwave
import time
import logging
import zmq
import os
import glob


def test():
    class handler:
        def __init__(self):
            self._last = time.time()

        def on_setup(self):
            port = 9876
            context = zmq.Context()
            self._socket = context.socket(zmq.PUB)
            self._socket.bind("tcp://*:%d" % port)

        def on_update(self, data):
            _now = time.time()
            if _now - self._last > .1:
                msg = ('{"time": %.2f,'
                       ' "raw": %.4f,'
                       ' "meditation": %.4f,'
                       ' "attention": %.4f}' % (
                           data['time'], data['raw'],
                           data['meditation'], data['attention']))
                print(msg)
                self._socket.send_string(msg)
                self._last = _now

    try:
        c = mindwave.connection(device='/dev/ttyUSB1', handler=handler())
    except mindwave.device_error as ex:
        logging.error(ex)
        print(glob.glob('/dev/ttyUSB*'))
        raise SystemExit(-1)
    c.autoconnect()
    while True:
        time.sleep(1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test()
    print('quit')
