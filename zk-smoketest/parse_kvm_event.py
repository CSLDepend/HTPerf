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
        self.tx_bytes_start = None
        self.tx_packets_start = None
        self.rx_bytes_start = None
        self.rx_packets_start = None
        self.tx_bytes_end = None
        self.tx_bytes_end = None
        self.rx_packets_end = None
        self.rx_packets_end = None

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
        else:
            m = re.search('^vnet0 rx_bytes (\d+)', line)
            if m:
                if not self.rx_bytes_start:
                    self.rx_bytes_start = long(m.group(1))
                else:
                    self.rx_bytes_end = long(m.group(1))
            m = re.search('^vnet0 tx_bytes (\d+)', line)
            if m:
                if not self.tx_bytes_start:
                    self.tx_bytes_start = long(m.group(1))
                else:
                    self.tx_bytes_end = long(m.group(1))
            m = re.search('^vnet0 rx_packets (\d+)', line)
            if m:
                if not self.rx_packets_start:
                    self.rx_packets_start = long(m.group(1))
                else:
                    self.rx_packets_end = long(m.group(1))
            m = re.search('^vnet0 tx_packets (\d+)', line)
            if m:
                if not self.tx_packets_start:
                    self.tx_packets_start = long(m.group(1))
                else:
                    self.tx_packets_end = long(m.group(1))

    # duration in usec
    def get_duration(self):
        count = len(self.events)
        if count == 0:
            print "Error: No event!"
            sys.exit()

        duration = self.events[count - 1] - self.events[0]
        return duration

    # get event arrival rate in seconds
    def get_rate(self):
        count = len(self.events)
        if count == 0:
            print "Error: No event!"
            sys.exit()

        return float(count)*USEC_PER_SEC/float(self.get_duration())

    # get rx throughput in bytes/seconds
    def get_rx_throughput_bytes(self):
        if not (self.rx_bytes_start or self.rx_bytes_end):
            print "No rx throughput data."
            sys.exit()

        return (self.rx_bytes_end - self.rx_bytes_start)*USEC_PER_SEC/float(self.get_duration())

    # get tx throughput in bytes/seconds
    def get_tx_throughput_bytes(self):
        if not (self.tx_bytes_start or self.tx_bytes_end):
            print "No tx throughput data."
            sys.exit()

        return (self.tx_bytes_end - self.tx_bytes_start)*USEC_PER_SEC/float(self.get_duration())

    # get rx throughput in packets/seconds
    def get_rx_throughput_packets(self):
        if not (self.rx_packets_start or self.rx_packets_end):
            print "No rx throughput data."
            sys.exit()

        return (self.rx_packets_end - self.rx_packets_start)*USEC_PER_SEC/float(self.get_duration())

    # get tx throughput in packets/seconds
    def get_tx_throughput_packets(self):
        if not (self.tx_packets_start or self.tx_packets_end):
            print "No tx throughput data."
            sys.exit()

        return (self.tx_packets_end - self.tx_packets_start)*USEC_PER_SEC/float(self.get_duration())

class ParseZKLatency:
    def __init__(self, in_file):
        self.test_info = {}
        with open(in_file) as fp:
            for line in fp:
                m = re.search("(\S+)\s+(\d+)\s+permanent.+\s(\d+\.\d+)/sec\)", line)
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
    tx_rates = Series2D(n_exps)
    rx_rates = Series2D(n_exps)
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

            rx_rates.append_to_row(
                n_idx, apic_write.get_rx_throughput_packets() * TIME_SCALE)
            tx_rates.append_to_row(
                n_idx, apic_write.get_tx_throughput_packets() * TIME_SCALE)

            apic_write_rates.append_to_row(n_idx, apic_write.get_rate())
            apic_read_rates.append_to_row(n_idx, apic_read.get_rate())
            pio_write_rates.append_to_row(n_idx, pio_write.get_rate())

            print "\tapic_write rate=%f/sec" % (apic_write.get_rate())
            print "\tapic_read rate=%f/sec" % (apic_read.get_rate())
            print "\tpio_write rate=%f/sec" % (pio_write.get_rate())

    # Graphing
    fig, ax = plt.subplots()

    index = np.arange(n_ops)
    bar_width = 1.0/8
    error_config = {'ecolor': '0.3'}

    opacity = 1

    req_rates.dump()

    with PdfPages(args.output_file) as pdf:
        plt.bar(index, req_rates.get_means(), bar_width,
                 alpha=opacity,
                 color='b',
                 # log=True,
                 yerr=req_rates.get_std(),
                 error_kw=error_config,
                 label='ZK request rates/' + args.latency_unit)

        plt.bar(index + bar_width, rx_rates.get_means(), bar_width,
                 alpha=opacity,
                 edgecolor='black',
                 color='y',
                 hatch='//',
                 yerr=rx_rates.get_std(),
                 error_kw=error_config,
                 label='VM RX packets/' + args.latency_unit)

        plt.bar(index + 2*bar_width, tx_rates.get_means(), bar_width,
                 alpha=opacity,
                 edgecolor='black',
                 color='r',
                 hatch='//',
                 yerr=tx_rates.get_std(),
                 error_kw=error_config,
                 label='VM TX packets/' + args.latency_unit)

        plt.bar(index + 3*bar_width, apic_read_rates.get_means(), bar_width,
                 alpha=opacity,
                 color='y',
                 log=args.log_scale,
                 yerr=apic_read_rates.get_std(),
                 error_kw=error_config,
                 label='APIC read rates/sec')

        plt.bar(index + 4*bar_width, apic_write_rates.get_means(), bar_width,
                 alpha=opacity,
                 color='r',
                 log=args.log_scale,
                 yerr=apic_write_rates.get_std(),
                 error_kw=error_config,
                 label='APIC write rates/sec')

        plt.bar(index + 5*bar_width, pio_write_rates.get_means(), bar_width,
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
        plt.xticks(index + 3*bar_width, operations)
        plt.legend(loc=2)

        # plt.tight_layout()
        pdf.savefig()
        plt.close()
