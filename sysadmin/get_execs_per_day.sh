#!/bin/bash

# Get the number of executions performed the last 30 days
find ~/ipolDevel/shared_folder/run -maxdepth 2 -type d -mtime -30 -printf "%T+\t%p\n"| echo "$(wc -l) / 30" | bc

