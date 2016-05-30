# pymindwave
Read and plot data from a NeuroSky MindWave Headset.

This repository contains three components:

* a Python3 module `mindwave` which communicates with a MindWave headset
* a CLI script which reads data from the above module and publishes them using **ZMQ**
* a **PyQt4**-UI which plots available data using **Qwt5**

There are projects like this already but the best way to get to know a gadget
is to program it on your own (and the other projects didn't work for me or where
poorly written :))


Description
-----------

![graph plotter screenshot](screenshot.png)


Get & Install
-------------

    git clone https://github.com/frans-fuerst/pymindwave.git
    pymindwave/reader_example.py

    # run a ZMQ based publisher with some messages on the command line
    pymindwave/reader_example.py

    # run the UI with Qwt plots (example only)
    mw_graphs_qt.py


Requirements
------------

* Python Python 3+
* `python3-zmq` (for both Python2 and Python3 if you have use Python2 for the UI like me)
* `pyserial`
* `PyQt4`
* `PyQt4.Qwt5`
* You might have get needed **permissions** for your user `usermod -a -G dialout <user>`


Todo
----
* read more available data
* support ID based connections
* make single threaded



