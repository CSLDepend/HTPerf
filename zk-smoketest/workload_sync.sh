#!/bin/bash
#
# usage ./workload_sync.sh output_dir

if [ $# -eq 0 ]; then
    echo "Please provide the output directory!"
fi
OUTPUT=$1

if [ -d $OUTPUT ]; then
    rm -rf $OUTPUT
fi

mkdir $OUTPUT
PYTHONPATH=lib.linux-x86_64-2.6 LD_LIBRARY_PATH=lib.linux-x86_64-2.6 ./zk-latencies.py --servers os1:2181 --znode_count=1000 --force --log_dir=$OUTPUT --synchronous &> $OUTPUT/latencies.txt
