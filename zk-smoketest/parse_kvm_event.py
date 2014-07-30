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

parser.add_argument('-m', '--min_experiment_index', action="store",
                    dest='min_exp_idx',
                    default=1, type=int)

parser.add_argument('-M', '--max_experiment_index', action="store",
                    dest='max_exp_idx',
                    default=1, type=int)

parser.add_argument('-Y', '--ylim_top', action="store",
                    dest='ylim_top',
                    default=100000, type=int)

parser.add_argument('-y', '--ylim_bottom', action="store",
                    dest='ylim_bottom',
                    default=0, type=int) 

parser.add_argument('-o', '--output', action="store",
                    dest='output_file',
                    default='plot.pdf' )

parser.add_argument('-u', '--latency_unit', action="store",
                    dest='latency_unit',
                    default='sec' )

parser.add_argument('-l', '--log_scale', action="store_true",
                    dest='log_scale',
                    default=False)
args = parser.parse_args()

USEC_PER_SEC = 1000000

class EventSeries:
    def __init__(self, pattern):
        self.event_pattern = re.compile(pattern)
        self.events = []
        self.parse_time = re.compile('.+\s(\d+)\.(\d+):\s.+')

    def try_add(self, line):
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

    # get event arrival rate in seconds
    def get_rate(self):
        count = len(self.events)
        if count == 0:
            print "Error: No event!"
            sys.exit()

        duration = self.events[count - 1] - self.events[0]

        # print "count=%d; duration=%d(usec)" % (count, duration) 

        return float(count)*USEC_PER_SEC/float(duration)

class ParseZKLatency:
    def __init__(self, in_file):
        self.test_info = {}
        with open(in_file) as fp:
            for line in fp:
                m = re.search("(\S+)\s+(\d+)\s+permanent.+(\d+\.\d+)/sec\)", line)
                if m:
                    self.znode_count = m.group(2)
                    self.test_info[m.group(1)] = float(m.group(3))
                    # print 'Added: (' + m.group(1) + ',' + m.group(3) + ')'


    def get_info(self, field):
        return self.test_info[field]

class Series2D:
    def __init__(self, ysize):
        self.data = [[] for y in range(ysize)]
        self.ysize = ysize

    def append_to_row(self, y, item):
        # print "Adding item %d to data[%d]." %(item, y-1)
        self.data[y].append(item)

    def get_means(self):
        return np.mean(self.data, axis=0)

    def get_std(self):
        return np.std(self.data, axis=0)

    def dump(self):
        print "DATA: "
        print self.data
        print "MEANS: "
        print self.get_means()
        print "STD: "
        print self.get_std()


if __name__ == '__main__':
    TIME_SCALE = 1.0
    if args.latency_unit == 'msec':
        TIME_SCALE = 0.0001

    operations = ['created', 'set', 'get', 'deleted']
    n_ops = len(operations)
    n_exps = args.max_exp_idx - args.min_exp_idx + 1
    req_rates = Series2D(n_exps)
    apic_write_rates = Series2D(n_exps)
    apic_read_rates = Series2D(n_exps)
    pio_write_rates = Series2D(n_exps)

    for exp_idx in range(args.min_exp_idx, args.max_exp_idx + 1):
        exp_name = args.input + str(exp_idx)
        latency_input = exp_name + '/latencies.txt'
        zk_latency = ParseZKLatency(latency_input)

        n_idx = exp_idx - args.min_exp_idx

        for ops in operations:
            print 'OPERATION: %s -- rate=%f/%s' % (ops, zk_latency.get_info(ops), args.latency_unit)
            req_rates.append_to_row(
                n_idx, zk_latency.get_info(ops) * TIME_SCALE)

            in_file = exp_name + '/' + ops + '.txt'
            with open(in_file) as fp:
                apic_write = EventSeries('apic_write')
                apic_read = EventSeries('apic_read')
                pio_write = EventSeries('pio_write')
                for line in fp:
                    apic_write.try_add(line)
                    apic_read.try_add(line)
                    pio_write.try_add(line)

            apic_write_rates.append_to_row(n_idx, apic_write.get_rate())
            apic_read_rates.append_to_row(n_idx, apic_read.get_rate())
            pio_write_rates.append_to_row(n_idx, pio_write.get_rate())

            print "\tapic_write rate=%f/sec" % (apic_write.get_rate())
            print "\tapic_read rate=%f/sec" % (apic_read.get_rate())
            print "\tpio_write rate=%f/sec" % (pio_write.get_rate())

    # Graphing
    fig, ax = plt.subplots()

    index = np.arange(n_ops)
    bar_width = 0.2
    error_config = {'ecolor': '0.3'}

    opacity = 0.4

    req_rates.dump()

    with PdfPages(args.output_file) as pdf:
        plt.bar(index, req_rates.get_means(), bar_width,
                 alpha=opacity,
                 color='b',
                 # log=True,
                 yerr=req_rates.get_std(),
                 error_kw=error_config,
                 label='ZK request rates/' + args.latency_unit)

        plt.bar(index + bar_width, apic_write_rates.get_means(), bar_width,
                 alpha=opacity,
                 color='r',
                 log=args.log_scale,
                 yerr=apic_write_rates.get_std(),
                 error_kw=error_config,
                 label='APIC write rates/sec')

        plt.bar(index + 2*bar_width, apic_read_rates.get_means(), bar_width,
                 alpha=opacity,
                 color='y',
                 log=args.log_scale,
                 yerr=apic_read_rates.get_std(),
                 error_kw=error_config,
                 label='APIC read rates/sec')

        plt.bar(index + 3*bar_width, pio_write_rates.get_means(), bar_width,
                 alpha=opacity,
                 color='g',
                 log=args.log_scale,
                 yerr=pio_write_rates.get_std(),
                 error_kw=error_config,
                 label='PIO write rates/sec')


        plt.gca().set_ylim(bottom=args.ylim_bottom, top=args.ylim_top)
        plt.xlabel('Operations')
        plt.ylabel('Rates')
        plt.title('Zookeeper Latency test')
        plt.xticks(index + bar_width, operations)
        plt.legend()

        # plt.tight_layout()
        pdf.savefig()
        plt.close()
