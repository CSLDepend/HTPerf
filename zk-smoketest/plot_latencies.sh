#!/bin/bash
#
# usage ./get_latencies.sh num_of_run

if [ $# -eq 0 ]
  then
    echo "Please provide the number of runs!"
fi

NRUNS=$1
SUFFIX='_delay5ms_'
#SUFFIX=''

echo "Ploting async..."
./parse_kvm_event.py -o rate_async_log${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='sec' --log_scale latency_async${SUFFIX}
./parse_kvm_event.py -o rate_async${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='sec' --ylim_top=50000 latency_async${SUFFIX}

for i in $(seq 1 $NRUNS); do
    ./plot_event_flows.py -o '_async'${SUFFIX}${i} -r 10 latency_async${SUFFIX}${i}
done

echo "Ploting sync..."
./parse_kvm_event.py -o rate_sync_log${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='sec' --log_scale latency_sync${SUFFIX}
./parse_kvm_event.py -o rate_sync${SUFFIX}.pdf -m 1 -M $NRUNS --latency_unit='sec' --ylim_top=50000 latency_sync${SUFFIX}

for i in $(seq 1 $NRUNS); do
    ./plot_event_flows.py -o '_sync'${SUFFIX}${i} -r 10 latency_sync${SUFFIX}${i}
done
