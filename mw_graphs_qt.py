#!/usr/bin/env python3

import zmq
import sys
import os
import threading
import logging
import time

from PyQt4 import QtGui, QtCore, Qt, uic
import PyQt4.Qwt5 as Qwt

LOG = logging.getLogger('mw_graph')

class mw_graphs(QtGui.QMainWindow):

    def __init__(self):

        class graph:
            def __init__(self, plot, title):
                self._plot = plot
                #self._plot.setCanvasBackground(Qt.black)
                self._plot.setAxisTitle(Qwt.QwtPlot.xBottom, 'Time')
                #self._plot.setAxisScale(Qwt.QwtPlot.xBottom, 0, 10, 1)
                self._plot.setAxisTitle(Qwt.QwtPlot.yLeft, title)
                #self._plot.setAxisScale(Qwt.QwtPlot.yLeft, 0, 250, 40)
                #self._plot.setAxisAutoScale(Qwt.QwtPlot.yLeft, True)
                #self._plot.setAxisAutoScale(Qwt.QwtPlot.xBottom, True)
                self._plot.replot()
                self._plot.enableAxis(Qwt.QwtPlot.xBottom, False)
                #self._plot.enableAxis(Qwt.QwtPlot.yLeft, False)

                self._xdata = []
                self._ydata = []
                self._curve = Qwt.QwtPlotCurve('')
                self._curve.setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
                #pen = QPen(QColor('limegreen'))
                #pen.setWidth(2)
                #self._curve.setPen(pen)
                #self._curve.setData(self._xdata, self._ydata)

                self._curve.attach(self._plot)

            def add_value(self, value):
                self._xdata.append(time.time())
                self._ydata.append(value)
                self._curve.setData(self._xdata, self._ydata)
                #self.plt_raw.setAxisScale(Qwt.QwtPlot.xBottom, self._xdata[0], self._xdata[-1])
                #self.plt_raw.setAxisScale(Qwt.QwtPlot.xBottom, self._xdata[0], self._xdata[-1])
                self._plot.replot()


        self._colors = [
            QtCore.Qt.green,
            QtCore.Qt.blue,
            QtCore.Qt.red,
            QtCore.Qt.cyan,
            QtCore.Qt.magenta,
            QtCore.Qt.darkBlue,
            QtCore.Qt.darkCyan,
            QtCore.Qt.darkGray,
            QtCore.Qt.darkGreen,
            QtCore.Qt.darkMagenta,
            QtCore.Qt.darkRed,
            QtCore.Qt.darkYellow,
            QtCore.Qt.lightGray,
            QtCore.Qt.gray,
            QtCore.Qt.white,
            QtCore.Qt.black,
            QtCore.Qt.yellow]

        QtGui.QMainWindow.__init__(self)

        self.setMouseTracking(True)
        self._directory = os.path.dirname(os.path.realpath(__file__))
        uic.loadUi(os.path.join(self._directory, 'mw_graphs_qt.ui'), self)

        self._idle_timer = QtCore.QTimer(self)

        self._graphs = {}
        self._graphs['raw'] = graph(self.plt_raw, 'Raw data')
        self._graphs['meditation'] = graph(self.plt_meditation, 'Meditation')
        self._graphs['attention'] = graph(self.plt_attention, 'Attention')

        _thread = threading.Thread(target=self._data_listener)
        _thread.daemon = True
        _thread.start()
        self.lst_messages.setVisible(False)

        self.show()

    def _data_listener(self):
        port = 9876
        context = zmq.Context()
        socket = context.socket(zmq.SUB)

        socket.connect ("tcp://localhost:%d" % port)
        socket.setsockopt(zmq.SUBSCRIBE, '')
        while True:
            msg = socket.recv_json()
            try:
                QtCore.QMetaObject.invokeMethod(
                    self, "_on_server_message",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(dict, msg))
            except AttributeError:
                pass

    @QtCore.pyqtSlot(dict)
    def _on_server_message(self, msg):
        print(msg)
        self._graphs['raw'].add_value(msg['raw'])
        self._graphs['meditation'].add_value(msg['meditation'])
        self._graphs['attention'].add_value(msg['attention'])


def main():
    logging.basicConfig(level=logging.INFO)

    LOG.info(sys.executable)
    LOG.info('.'.join((str(e) for e in sys.version_info)))

    app = QtGui.QApplication(sys.argv)
    ex = mw_graphs()

#    for s in (signal.SIGABRT, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
#        signal.signal(s, lambda signal, frame: sigint_handler(signal, ex))

    # catch the interpreter every now and then to be able to catch signals
    timer = QtCore.QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

