#!/bin/bash
#
# usage ./get_latencies.sh num_of_run

if [ $# -eq 0 ]
  then
    echo "Please provide the number of runs!"
fi

NRUNS=$1
SUFFIX='_delay100ms_'

echo "Ploting async..."
./parse_kvm_event.py -o plot_async_log.pdf -m 1 -M $NRUNS --latency_unit='sec' --log_scale latency_async${SUFFIX}
./parse_kvm_event.py -o plot_async.pdf -m 1 -M $NRUNS --latency_unit='sec' latency_async${SUFFIX}


echo "Ploting sync..."
./parse_kvm_event.py -o plot_sync_log.pdf -m 1 -M $NRUNS --latency_unit='sec' --log_scale latency_sync${SUFFIX}
./parse_kvm_event.py -o plot_sync.pdf -m 1 -M $NRUNS --latency_unit='sec' latency_sync${SUFFIX}
