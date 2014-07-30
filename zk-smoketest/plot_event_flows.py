#!/usr/bin/env python

# Metrics 
#       - event/sec
#       - inter-arrival rate
#
# Events of interest
#       - apic write
#       - apic read
#       - pio write
#
# Input
#       Data get from /sys/kernel/debug/tracing/trace_pipe
#

import sys, re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('input', help='input file')

parser.add_argument('-o', '--output_suffix', action="store",
                    dest='output_suffix',
                    default='' )

parser.add_argument('-r', '--resolution', action="store",
                    dest='resolution',
                    default=10,
                    type=int)

parser.add_argument('-M', '--max_timeline', action="store",
                    dest='max_ts',
                    default=sys.maxsize,
                    type=int)

parser.add_argument('-l', '--log_scale', action="store_true",
                    dest='log_scale',
                    default=False)
args = parser.parse_args()

USEC_PER_SEC  = 1000000
USEC_PER_MSEC = 1000

class EventSeries:
    def __init__(self, pattern):
        self.event_pattern = re.compile(pattern)
        self.events = []
        self.parse_time = re.compile('.+\s(\d+)\.(\d+):\s.+')
        self.first_event = None

    def try_add(self, line):
        if not self.first_event:
            m = self.parse_time.search(line)
            if m:
                ts_sec = m.group(1)
                ts_usec = m.group(2)
                try:
                    usec = long(ts_usec) + USEC_PER_SEC*long(ts_sec)
                    self.first_event = usec
                except ValueError:
                    print "Wrong format."
                    sys.exit()
            
        if self.event_pattern.search(line):
            m = self.parse_time.search(line)
            if not m:
                print "Wrong format."
                sys.exit()

            ts_sec = m.group(1)
            ts_usec = m.group(2)
            try:
                usec = long(ts_usec) + USEC_PER_SEC*long(ts_sec)
                self.events.append(usec)
                # print "Added: " + line
            except ValueError:
                print "Wrong format."
                sys.exit()

    # get event arrival throughput in seconds
    def get_throughput(self):
        count = len(self.events)
        if count == 0:
            print "Error: No event!"
            sys.exit()

        duration = self.events[count - 1] - self.events[0]

        # print "count=%d; duration=%d(usec)" % (count, duration) 

        return float(count)*USEC_PER_SEC/float(duration)

    # resolution in msec
    def get_time_series(self, resolution=10):
        ts = []
        win_start = self.first_event
        win_end = self.first_event + resolution*USEC_PER_MSEC
        count = 0

        while self.events[0] > win_end:
            ts.append(0)
            win_start = win_end
            win_end += resolution*USEC_PER_MSEC

        for evt in self.events:
            if evt >= win_start:
                if evt < win_end:
                    count += 1
                else:
                    ts.append(count)
                    count = 0
                    win_start = win_end
                    win_end += resolution*USEC_PER_MSEC
        return ts

if __name__ == '__main__':

    operations = ['created', 'set', 'get', 'deleted']
    n_ops = len(operations)

    exp_name = args.input
    RES = args.resolution

    for ops in operations:
        in_file = exp_name + '/' + ops + '.txt'
        with open(in_file) as fp:
            apic_write = EventSeries('apic_write')
            apic_read = EventSeries('apic_read')
            pio_write = EventSeries('pio_write')
            for line in fp:
                apic_write.try_add(line)
                apic_read.try_add(line)
                pio_write.try_add(line)

        print "\tapic_write:%s" % (apic_write.get_time_series())
        print "\tapic_read: %s" % (apic_read.get_time_series())
        print "\tpio_write: %s" % (pio_write.get_time_series())

        # Graphing
        with PdfPages(ops + args.output_suffix + '.pdf') as pdf:
            apic_write_ts = apic_write.get_time_series(RES)
            x_axis = len(apic_write_ts)*RES
            if args.max_ts < x_axis:
                x_axis = args.max_ts
            apic_write_xaxis = np.arange(0, x_axis, RES)

            print "x=%d; y=%d" % (len(apic_write_xaxis), len(apic_write_ts[:x_axis/RES]))

            plt.plot(apic_write_xaxis, apic_write_ts[:x_axis/RES],
                     'b-', label='APIC write')


            apic_read_ts = apic_read.get_time_series(RES)
            x_axis = len(apic_read_ts)*RES
            if args.max_ts < x_axis:
                x_axis = args.max_ts
            apic_read_xaxis = np.arange(0, x_axis, RES)

            plt.plot(apic_read_xaxis, apic_read_ts[:x_axis/RES],
                     'r-', label='APIC read')


            pio_write_ts = pio_write.get_time_series(RES)
            x_axis = len(pio_write_ts)*RES
            if args.max_ts < x_axis:
                x_axis = args.max_ts
            pio_write_xaxis = np.arange(0, x_axis, RES)

            plt.plot(pio_write_xaxis, pio_write_ts[:x_axis/RES],
                     'y-', label='PIO write')

            if args.log_scale:
                plt.yscale('log')

            plt.xlabel('time (msec)')
            plt.ylabel('throughput /' + str(RES) + 'msec')
            plt.grid(True)
            plt.legend()
            pdf.savefig()
            plt.close()





















