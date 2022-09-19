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
                    stacking='selected', addtext='', start_hour=20, end_hour=6):
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
    resample = 4 # resample factor
    df = df.resample(f'{resample}T').sum() # resample 3 min, summing where there was no data it uses 0        
    df['nchange_pixels'] = 100*df['nchange_pixels']/body_pixels # just nomalize by max movement    
    # setting unique night identifier as date of start of the night
    # from 20:00 to 6:00 are 10 hours -
    night_span = 24-start_hour+end_hour
    timedate_shifted = (df.index - datetime.timedelta(hours=start_hour))
    df['night_day'] = timedate_shifted.date
    df['night_time'] = timedate_shifted.time
    if verbose: # stair-step night code plot and span of movement
        plt.figure()
        df.span.apply(lambda x: x/60.).hist(bins=40)  
        df['night_day'].map(lambda x: int(x.month*100 + x.day)).plot()        
    nights =  []    
    nights_info = []     
    nsamples = (60//resample)*night_span+1 # number of samples per night [20, 6] +1 to close to the rigth
    print(f'nights - span: {night_span} length: {nsamples}')
    for night, dfnight in df.groupby(df.night_day):         
        night_data = dfnight[ dfnight.night_time <= datetime.time(hour=night_span) ]['nchange_pixels']        
        if len(night_data) != nsamples:
            print(f"ignored night data { night } len {len(night_data)}")
            continue 
        nights.append(night_data)
        nights_info.append([night.strftime("%m/%d"), np.sum(night_data.values), np.count_nonzero(night_data.values)])
    # plot number of last nights defined    
    ngraphs = nnights+1 if stacking else nnights    
    _ , axis = plt.subplots(ngraphs,1,figsize=(15,4*ngraphs)) 
    last_nights = nights[-nnights:]     # latests nights 
    nights_info = [ param[0] for param in nights_info[-nnights:]]
    def plot_night(axis, serie, label, ylim=True, ylabel=True):
        xs = np.arange(len(serie))
        xtick_labels = list(range(start_hour, 24)) + list(range(0, end_hour+1)) # hours labels 
        xticks_xs = np.linspace(0, len(serie), len(xtick_labels)) # hours positions
        axis.plot(xs, serie.values, linewidth=0.3, color='b', label=label)                      
        axis.fill_between(xs, serie.values, 0, color='gray', alpha=0.5)
        smoothed = serie.rolling(window=5).mean().values
        axis.plot(xs, smoothed, linewidth=0.5, color='r', alpha=0.5)       
        axis.fill_between(xs, smoothed, 0)
        axis.grid()
        if not ylim:
            miny, maxy = np.percentile(serie.values, [1, 99])
            axis.set_ylim(miny, maxy)
            print(f"p% and p9% - min {miny} and max {maxy}")
        else:
            axis.set_ylim(0, 100)                
        if ylabel:
            axis.set_ylabel('% Moving Kid')  
        # set xtick positions and labels 
        axis.set_xticks(xticks_xs)
        axis.set_xticks(xticks_xs+0.5*(xticks_xs[1]-xticks_xs[0]), minor=True)
        axis.set_xticklabels(xtick_labels)       
        axis.legend(fontsize=16) 
    for i, night_data in enumerate(last_nights):  
        plot_night(axis[i], night_data, 'night of day '+nights_info[i]+' '+addtext)
    if stacking: # stack to see any underline pattern        
        i=i+1 # last graph 
        if 'selected' in stacking:
            nights = nights[-nnights:]         
        sum = nights[0].values 
        for night in nights[1:]:  # stack = summing 
            sum += np.nan_to_num(night.values)
        sum = sum/len(nights)
        plot_night(axis[i], pd.Series(sum), 'stacked nights', ylim=False, ylabel=False)                  
        print(f" stacked {len(nights)} series")
    return df 


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