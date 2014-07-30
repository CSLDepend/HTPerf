#!/bin/bash
#
# usage ./get_latencies.sh num_of_run

if [ $# -eq 0 ]
  then
    echo "Please provide the number of runs!"
fi

NRUNS=$1
SUFFIX='_delay10ms_'

echo "Warming up..."
./workload.sh test

for i in $(seq 1 $NRUNS); do
    sleep 5
    echo "Run async $i..."
    ./workload.sh latency_async${SUFFIX}${i}
done

rm -rf test

echo "Ploting async..."
./parse_kvm_event.py -o plot_async${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='msec' latency_async${SUFFIX}


for i in $(seq 1 $NRUNS); do
    sleep 5
    echo "Run sync $i..."
    ./workload_sync.sh latency_sync${SUFFIX}${i}
done

rm -rf test

echo "Ploting sync..."
./parse_kvm_event.py -o plot_sync${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='msec' latency_sync${SUFFIX}
