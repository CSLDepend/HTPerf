#!/bin/bash
if [ -d test ]; then
    rm test
fi

mkdir test
PYTHONPATH=lib.linux-x86_64-2.6 LD_LIBRARY_PATH=lib.linux-x86_64-2.6 ./zk-latencies.py --servers os1:2181 --znode_count=10000 --force --log_dir=test