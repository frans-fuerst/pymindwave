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
            self._output_file = None
            self._start = time.time()

        def on_update(self, data):
            if data['status'] != 'connected':
                return
            if self._output_file is None:
                self._output_file = open(time.strftime('%Y%m%d-%H%M%S.log'), 'w')

            _now = time.time()
            if _now - self._last < .05:
                return
            _duration = _now - self._start
            msg = ('{"time": %.2f,'
                   ' "duration": %.4f,'
                   ' "raw": %.4f,'
                   ' "heart_rate": %.4f,'
                   ' "meditation": %.4f,'
                   ' "attention": %.4f,'
                   ' "eeg": %s}' % (
                       data['time'], _duration, data['raw'], data['heart_rate'],
                       data['meditation'], data['attention'],
                       data['eeg'])).replace("'", '"')
            print(msg)
            self._socket.send_string(msg)
            self._output_file.write(msg)
            self._output_file.write('\n')
            self._last = _now

    try:
        devices = glob.glob('/dev/ttyUSB*')
        if len(devices) > 0:
            c = mindwave.connection(device=devices[0], handler=handler())
        else:
            raise Exception('no devices found')
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
            print("headset status: ", status)
        time.sleep(1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test()
    print('quit')
