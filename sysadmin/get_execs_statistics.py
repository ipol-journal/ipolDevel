#!/usr/bin/python

'''
Count the number of executions the last 30 days
'''

import os
import datetime

DAYS = 30

base_dir = os.path.expanduser("~/ipolDevel/shared_folder/run")
demos = os.listdir(base_dir)

now = datetime.datetime.now()
date_from = now - datetime.timedelta(days=DAYS)

results = {}
#
for demo_id in demos:
    demo_dir = os.path.join(base_dir, demo_id)

    if demo_id == '-1':
        continue # Test demo

    if demo_id.startswith('.'):
        continue # Hidden folder

    # Get the executions of this demo
    execs = os.listdir(demo_dir)
    
    count = 0
    for execution in execs:
        execution_dir = os.path.join(demo_dir, execution)
        
        st_mtime = os.stat(execution_dir).st_mtime
        exec_datetime = datetime.datetime.fromtimestamp(st_mtime)

        if exec_datetime > date_from:
            count += 1

    results[demo_id] = count
        
    #print "demo #{}:\t{}\t({}/day)".format(demo_id, count, int(count/30.0))

print "Execution statistics of the demos the last {} days".format(DAYS)

count_total = 0
#
for demo_id in sorted(results, key=results.get, reverse=True):
    count = results[demo_id]
    count_total += count
    print "demo #{}:\t{}\t({}/day)".format(demo_id, count, int(float(count)/DAYS))

print
print "Total:\t{}\t({}/day)".format(count_total, int(float(count_total)/DAYS))
