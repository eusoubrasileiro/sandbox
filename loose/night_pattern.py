import pandas as pd
import numpy as np
import datetime 
from matplotlib import pylab as plt
import datetime
import pandas as pd
import numpy as np
import datetime 
import os, datetime
import sqlite3
import subprocess


def plot_nights(df, body_pixels, cam_name='frontwall', verbose=False, nnights=1,
                    stacking='selected', addtext=''):
    """
        Assumptions: a. nothing besides the child is moving inside the room.  
        Warning: Somes days the FAN is ON making the curtain move and some days not.

        * body_pixels : aproximated number of pixels of a bounding box 
        around the child when she is standing up  
          
        hint: copy a motion picture snapshot and use gimp histogram to count pixels.
        
        * stacking: str 
            'selected' only stack selected nights (default)
            'all' stack everything on the database
            '' empty don't stack anything 
        
    """
    df = df[df['name'] == cam_name]
    df = df[['nchange_pixels', 'span']]
    if verbose:
        plt.figure()
        df.span.apply(lambda x: x/60.).hist(bins=40)    
    resample = 3 # resample factor
    dfp = df.resample(f'{resample}T').sum() # resample 3 min, summing where there was no data it uses 0        
    dfp['nchange_pixels'] = 100*dfp['nchange_pixels']/body_pixels # just nomalize by max movement    
    # setting unique night identifier as date of start of the night
    # def get_night(datetime_):
    #     pass 
    dfp['night'] = np.nan  # which sleep night are we in
    pday = None # start day date 
    for index in dfp.index:
        cday, chour = index.date(), index.time().hour
        if pday is None: # get start day date
            # correction for start day date only after 0:00
            pday = cday if chour > 18 else cday-pd.Timedelta(days=1)
            continue 
        if cday == pday+pd.Timedelta(days=1) and chour >= 12:  # next day morning ended
            pday = cday # starting new day
        dfp.at[index, 'night'] =  pday              
    if verbose: # stair-step night code plot
        plt.figure()
        dfp['night'].map(lambda x: int(x.month*100 + x.day)).plot()
    nights =  []    
    nights_info = []     
    night_start_hour = 20 
    night_end_hour = 6 # from 20:00 to 6:00 are 10 hours -
    nsamples = (60//resample)*(24-night_start_hour+night_end_hour) # number of samples per night 
    for night, dfnight in dfp.groupby(dfp.night)['nchange_pixels']:     
        night_data = dfnight[ ( (dfnight.index.time >= datetime.time(hour=night_start_hour)) & (dfnight.index.time < datetime.time(hour=23, minute=59, second=59)) ) | 
            ( (dfnight.index.time > datetime.time(hour=0)) & (dfnight.index.time <= datetime.time(hour=night_end_hour)) ) ]
        if len(night_data) != nsamples:
            print(f"ignored night data { night } len {len(night_data)}")
            continue 
        nights.append(night_data)
        nights_info.append([night.strftime("%m/%d"), night_data.index.time[0], night_data.index.time[-1], 
            np.sum(night_data.values), np.count_nonzero(night_data.values), night_data.size])
    # plot number of last nights defined    
    ngraphs = nnights+1 if stacking else nnights    
    fig, axis = plt.subplots(ngraphs,1,figsize=(15,4*ngraphs)) 
    last_nights = nights[-nnights:]     # latests nights 
    nights_info = [ param[0] for param in nights_info[-nnights:]]
    for i, night_data in enumerate(last_nights):        
        axis[i].plot(night_data.index.values, night_data.values, linewidth=0.3, color='b', label='night of day '+nights_info[i]+' '+addtext)                      
        axis[i].fill_between(night_data.index, night_data.values, 0, color='gray', alpha=0.5)
        smoothed = night_data.rolling(window=5).mean().values
        axis[i].plot(night_data.index.values, smoothed, linewidth=0.5, color='r', alpha=0.5)       
        axis[i].fill_between(night_data.index, smoothed, 0)
        axis[i].grid()
        axis[i].set_ylim(0, 100)        
        axis[i].set_ylabel('% Dancing Kid')  
        # We need to draw the canvas, otherwise the labels won't be positioned and - won't have values yet.
        fig.canvas.draw()
        # remove date from tick labels
        ticks = [ t.get_text().split()[-1] for t in axis[i].get_xticklabels() ]
        axis[i].set_xticklabels(ticks)
        axis[i].legend(fontsize=18)    
    if stacking: # stack to see any underline pattern        
        i=i+1 # last graph 
        if 'selected' in stacking:
            nights = last_nights         
        sum = nights[0].values 
        for night in nights[1:]:  # stack = summing 
            sum += night.values
        sum = sum/len(nights)
        axis[i].plot(night.index, sum, color='b', linewidth=0.3, label='stacked nights')
        axis[i].set_ylim(min(sum), max(sum))
        axis[i].fill_between(night.index, sum, 0, color='gray', alpha=0.5)
        def moving_average(x, w):
            return np.append(np.zeros(w-1), np.convolve(x, np.ones(w), 'valid') / w)
        smoothed = moving_average(sum, 5)
        axis[i].plot(night.index, smoothed, linewidth=0.5, color='r', alpha=0.5)       
        axis[i].fill_between(night.index, smoothed, 0)
        axis[i].grid()
        axis[i].legend(fontsize=18)
        fig.canvas.draw()
        # remove date from tick labels
        ticks = [ t.get_text().split()[-1] for t in axis[i].get_xticklabels() ]
        axis[i].set_xticklabels(ticks)
        print(f" stacked {len(nights)} series")
    return dfp 


# TODO make twin axis were right is labeled
# [sleeping, rolling, standing, dancing] to equivalent % of the
# other axis
# import numpy as np
# import matplotlib.pyplot as plt
# x = np.arange(0, 10, 0.1)
# y1 = 0.05 * x**2
# y2 = -1 *y1

# fig, ax1 = plt.subplots()

# ax2 = ax1.twinx()
# ax1.plot(x, y1, 'g-')
# ax2.plot(x, y2, 'b-')

# ax1.set_xlabel('X data')
# ax1.set_ylabel('Y1 data', color='g')
# ax2.set_ylabel('Y2 data', color='b')

# plt.show()

if __name__ == "__main__":
    dbpath = '/media/andre/Data/Downloads/motion.db'
    if os.path.exists(dbpath):
        os.remove(dbpath)    
    os.chdir(os.path.dirname(dbpath))
    _ = subprocess.run("wget ipcam.home/motion.db", shell=True,  check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Create your connection.
    cnx = sqlite3.connect('/media/andre/Data/Downloads/motion.db')
    df = pd.read_sql_query("SELECT * FROM events", cnx)
    df.dropna(inplace=True)
    df['span'] = (df.stop - df.start).astype(np.int32)
    from_utc_timestamp = lambda dts: pd.to_datetime(dts-10800, unit='s')# convert from utc to zone BR/SP -3:00
    df['start'] = from_utc_timestamp(df['start'])
    df['stop'] = from_utc_timestamp(df['stop'])
    df.set_index('start',inplace=True)
    df.sort_index(inplace=True)
    df['tstart'] = df.index.map(lambda x: int(x.timestamp())) # timestamp start 
    df.drop(['row_id', 'mfile', 'pfile', 'cam'], axis=1, inplace=True)
    # child sleep select - body_pixels (2nd argument) should be calibrated everytime the camera is repositioned
    plot_nights(df, 4e3, 'frontwall', nnights=7, stacking='selected', addtext="Daniel") 
    plot_nights(df, 30e3, 'street', nnights=3, stacking='all', addtext="Street") 
    plot_nights(df, 2.5e3, 'new', nnights=5, stacking='selected', addtext="Sarah") 
    plt.show()