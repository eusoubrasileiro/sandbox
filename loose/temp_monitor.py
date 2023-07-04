"""
Uses TEMPer2 sensor from https://pcsensor.com/manuals-detail?article_id=474 
to monitor temperature at our house. Writes on a database sqlite internal 
(sensor temperature) and external temperature (probe on the end of black wire)
"""

import pandas as pd 
import subprocess 
import time
from datetime import datetime
import sqlite3

# in case no permissions
#sudo chmod o+rw /dev/hidraw4

dbfile = '/home/andre/Projects/sandbox/loose/home_temperature.db'
temperpy_exec = '/home/andre/Projects/temper/temper.py'

while True:
    res = subprocess.run(temperpy_exec, shell=True,  check=True, capture_output=True)
    temp_in, temp_out = res.stdout.decode().split(' ')[-6][:-1], res.stdout.decode().split(' ')[-3][:-1]
    now = datetime.now()
    with sqlite3.connect(dbfile) as conn:
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO home (time, temp_out, temp_in) VALUES (?, ?, ?)", (datetime.now(), float(temp_out), float(temp_in)))
        conn.commit()    
    time.sleep(60*5) # every 5 minutes