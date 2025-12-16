"""
 Copyright (c) 2014, 2020, Oracle and/or its affiliates. 

NAME:
    Threads - Basic functionality

FUNCTION:
    Provide basic/core API for managing Threads

NOTE:
    None

History:
    mirivier    08/21/2014 - Create file
    ndesanto    10/02/2019 - 30374491 - EXACC PYTHON 3 MIGRATION BATCH 01 
"""

from __future__ import print_function

import signal

class exaBoxThreads(object):

    def __init__(self):
        pass

def alarm_handler(signum, frame):
    print('Received SIGNAL:', signum)
    raise Exception('SIGNAL Exception Aborting')

class exaBoxTimeout(object):

    def __init__(self, aTimeOut=10 ):

        self.__timeout = aTimeOut

    def mStart(self):
        signal.signal( signal.SIGALRM, alarm_handler)
        signal.alarm( self.__timeout)

    def mStop(self):
        pass
#
# Thread hang detection facility
#
import sys
import threading
try:
    try:
        from threading import _get_ident as get_ident
    except ImportError:
        from threading import get_ident
except ImportError:
    from _thread import get_ident
import linecache
import time
#
# Global timeout and sampling frequency values are in second
#
gTimeOut    = 10
gFreqPerSec = 10

def frame2string(frame):
    # from module traceback
    lineno = frame.f_lineno # or f_lasti
    co = frame.f_code
    filename = co.co_filename
    name = co.co_name
    s = '  File "{}", line {}, in {}'.format(filename, lineno, name)
    line = linecache.getline(filename, lineno, frame.f_globals).lstrip()
    return s + '\n\t' + line

def thread2list(frame):
    l = []
    while frame:
        l.insert(0, frame2string(frame))
        frame = frame.f_back
    return l

def ebThreadMonitor():

    global gTimeOut, gFreqPerSec
    print('### gTimeOut/gFreqPerSec:',gTimeOut,gFreqPerSec)
    self = get_ident()
    old_threads = {}
    while 1:
        time.sleep(1. / gFreqPerSec)
        now = time.time()
        then = now - gTimeOut
        frames = sys._current_frames()
        new_threads = {}
        for frame_id, frame in list(frames.items()):
            new_threads[frame_id] = thread2list(frame)
        for thread_id, frame_list in list(new_threads.items()):
            if thread_id == self: continue
            if thread_id not in old_threads or \
               frame_list != old_threads[thread_id][0]:
                new_threads[thread_id] = (frame_list, now)
            elif old_threads[thread_id][1] < then:
                print_frame_list(frame_list, frame_id)
            else:
                new_threads[thread_id] = old_threads[thread_id]
        old_threads = new_threads

def print_frame_list(frame_list, frame_id):
    sys.stderr.write('-' * 20 +
                     'Thread {}'.format(frame_id).center(20) +
                     '-' * 20 +
                     '\n' +
                     ''.join(frame_list))

def ebThreadStartHangMonitoring(aTimeOut=10):

    global gTimeOut
    gTimeOut = aTimeOut
    thread = threading.Thread(target=ebThreadMonitor)
    thread.daemon = True
    thread.start()
    return thread
#
# module self auto test
#
if __name__ == '__main__':
    ebThreadStartHangMonitoring()
    gTimeOut = 1
    time.sleep(3) # TEST
