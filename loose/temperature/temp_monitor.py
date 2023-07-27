"""
Uses TEMPer2 sensor from https://pcsensor.com/manuals-detail?article_id=474 
to monitor temperature at our house. Writes on a database sqlite internal 
(sensor temperature) and external temperature (probe on the end of black wire)

Uses https://github.com/ccwienk/temper.git

for jetson-nano or other arm use https://conda-forge.org/miniforge/
"""

import pandas as pd 
import subprocess 
import time
from datetime import datetime
import sqlite3

# in case no permissions
# sudo chmod o+rw /dev/hidraw4

dbfile = '/home/andre/home_temperature.db'
temperpy_exec = '/home/andre/temper/temper.py'

while True:    
    cmd = '/home/andre/miniforge-pypy3/bin/python3 /home/andre/temper/temper.py'.split()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True) 
    temp_in, temp_out = res.stdout.decode().split(' ')[-6][:-1], res.stdout.decode().split(' ')[-3][:-1]
    now = datetime.now()
    with sqlite3.connect(dbfile) as conn:
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO home (time, temp_out, temp_in) VALUES (?, ?, ?)", (datetime.now(), float(temp_out), float(temp_in)))
        conn.commit()    
    time.sleep(60*5) # every 5 minutes