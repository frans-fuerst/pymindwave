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
            self._output_file = open(time.strftime('%Y%m%d-%H%M%S.log'), 'w')

        def on_update(self, data):
            if data['status'] != 'connected':
                return
            _now = time.time()
            if _now - self._last > .05:
                msg = ('{"time": %.2f,'
                       ' "raw": %.4f,'
                       ' "meditation": %.4f,'
                       ' "attention": %.4f}' % (
                           data['time'], data['raw'],
                           data['meditation'], data['attention']))
                print(msg)
                self._socket.send_string(msg)
                self._output_file.write(msg)
                self._output_file.write('\n')
                self._last = _now

    try:
        c = mindwave.connection(device='/dev/ttyUSB1', handler=handler())
    except mindwave.device_error as ex:
        logging.error(ex)
        print(glob.glob('/dev/ttyUSB*'))
        raise SystemExit(-1)
    old_status = None
    while True:
        status = c.get_status()
        if status == 'standby' and old_status != status:
            c.autoconnect()
            old_status = status
        if not status == 'connected':
            print(status)
        time.sleep(1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test()
    print('quit')
