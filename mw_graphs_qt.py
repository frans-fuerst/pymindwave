#!/usr/bin/env python2

import zmq
import sys
import json
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
                self._plot.setMaximumHeight(100)
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

                scaleWidget = plot.axisWidget(Qwt.QwtPlot.yLeft)
                #scaleWidget.setFixedWidth(200)
                #d = scaleWidget.scaleDraw()
                #d.minimumExtent
                scaleWidget.scaleDraw().setMinimumExtent(100)

                self._curve.attach(self._plot)

            def add_value(self, t, value):
                if len(self._ydata) > 0 and self._ydata[-1] == value:
                    return
                self._xdata.append(t)
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
        self._graphs['raw']        = graph(self.plt_raw, 'raw data')
        self._graphs['meditation'] = graph(self.plt_meditation, 'meditation')
        self._graphs['attention']  = graph(self.plt_attention, 'attention')
        self._graphs['delta']      = graph(self.plt_delta, 'delta')
        self._graphs['theta']      = graph(self.plt_theta, 'theta')
        self._graphs['low_alpha']  = graph(self.plt_low_alpha, 'alpha_low')
        self._graphs['high_alpha'] = graph(self.plt_high_alpha, 'alpha_high')
        self._graphs['low_beta']   = graph(self.plt_low_beta, 'beta_low')
        self._graphs['high_beta']  = graph(self.plt_high_beta, 'beta_high')
        self._graphs['low_gamma']  = graph(self.plt_low_gamma, 'gamma_low')
        self._graphs['mid_gamma']  = graph(self.plt_high_gamma, 'gamma_mid')
        self.plt_raw.enableAxis(Qwt.QwtPlot.xBottom, True)
        self.plt_raw.setMaximumHeight(200)

        self._t_start = time.time()

        #self.plt_heart_rate.setVisible(False)
        _thread = threading.Thread(target=self._data_listener)
        _thread.daemon = True
        _thread.start()

        self.show()

    def _data_listener(self):
        if len(sys.argv) > 1:
            for l in open(sys.argv[1]).readlines():
                QtCore.QMetaObject.invokeMethod(
                    self, "_on_server_message",
                    QtCore.Qt.QueuedConnection,
                    QtCore.Q_ARG(dict, json.loads(l)))

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
        #print(msg)
        t = time.time() - self._t_start
        self.lbl_battery.setText("%d" % msg['battery'])
        self.lbl_heart_rate.setText("%d" % msg['heart_rate'])

        self._graphs['raw'].add_value(t, msg['raw'])
        self._graphs['meditation'].add_value(t, msg['meditation'])
        self._graphs['attention'].add_value(t, msg['attention'])
        try:
            self._graphs['delta'].add_value(t, msg['eeg']['delta'])
            self._graphs['theta'].add_value(t, msg['eeg']['theta'])
            self._graphs['low_alpha'].add_value(t, msg['eeg']['low_alpha'])
            self._graphs['high_alpha'].add_value(t, msg['eeg']['high_alpha'])
            self._graphs['low_beta'].add_value(t, msg['eeg']['low_beta'])
            self._graphs['high_beta'].add_value(t, msg['eeg']['high_beta'])
            self._graphs['low_gamma'].add_value(t, msg['eeg']['low_gamma'])
            self._graphs['mid_gamma'].add_value(t, msg['eeg']['mid_gamma'])
        except KeyError:
            pass


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

