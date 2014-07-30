#!/bin/bash
#
# usage ./get_latencies.sh num_of_run

if [ $# -eq 0 ]
  then
    echo "Please provide the number of runs!"
fi

NRUNS=$1
SUFFIX='_delay100ms_'
#SUFFIX=''

echo "Ploting async..."
./parse_kvm_event.py -o rate_async_log${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='sec' --log_scale latency_async${SUFFIX}
./parse_kvm_event.py -o rate_async${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='sec' --ylim_top=50000 latency_async${SUFFIX}


echo "Ploting sync..."
./parse_kvm_event.py -o rate_sync_log${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='sec' --log_scale latency_sync${SUFFIX}
./parse_kvm_event.py -o rate_sync${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='sec' --ylim_top=50000 latency_sync${SUFFIX}
