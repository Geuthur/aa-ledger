#!/bin/bash
max_mem=$1
cur_mem=$(</sys/fs/cgroup/memory.current)
health_file="/tmp/health.stat"
if [ -f "$health_file" ]; then
    echo "$health_file exists."
else
    echo "$health_file does not exist. Creating"
    echo 0 > "$health_file"
fi
health=$(<$health_file)
echo "Testing Mem: $cur_mem / $max_mem"
if [[ max_mem -gt cur_mem ]]
then
    echo 0 > "$health_file"
    echo "All Ok"
    exit 0
else
    new_val=$((1+$health))
    echo "Un-healthy! Check #$new_val"
    echo $new_val > "$health_file"
    if (($new_val > 3)); then
        echo "Starting a restart of this the container..."
        kill -SIGTERM 1
    fi
    exit 1
fi
