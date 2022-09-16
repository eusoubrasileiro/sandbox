import pandas as pd
import numpy as np
import datetime 
from matplotlib import pylab as plt
import datetime


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
    dance_pixels = 2*body_pixels
    #dfp['nchange_pixels'] += 1 # to avoid log of 0
    dfp['nchange_pixels'] = 100*dfp['nchange_pixels']/dance_pixels # just nromalize by max movment    
    date = dfp.index[0] # only for sorted datetimes
    hour = dfp.index[0].time().hour 
    if hour < 18: # correction for start data only after 0:00
        date = date-pd.Timedelta(days=1)
    date = date.date()
    dfp['night'] = np.nan  # which sleep night are we in
    for index, row in dfp.iterrows():
        cdate = index.date()
        chour = index.time().hour
        if cdate == date and chour > 18: # same night 
            dfp.at[index, 'night'] = date
        elif cdate == date+pd.Timedelta(days=1) and chour < 8:  # next morning
            dfp.at[index, 'night'] =  date  
        else:
            date = cdate 
            dfp.at[index, 'night'] =  date      
    if verbose: # stair-step night code plot
        plt.figure()
        dfp['night'].map(lambda x: int(x.month*100 + x.day)).plot()
    nights =  []    
    msgs = [] 
    nights_info = []
    # from 20:00 to 6:00 are 10 hours - 
    nsamples = (60//resample)*10 # number of samples per night 
    for night, dfnight in dfp.groupby(dfp.night)['nchange_pixels']:     
        night_data = dfnight[ ( (dfnight.index.time >= datetime.time(hour=20)) & (dfnight.index.time < datetime.time(hour=23, minute=59, second=59)) ) | 
            ( (dfnight.index.time > datetime.time(hour=0)) & (dfnight.index.time <= datetime.time(hour=6)) ) ]
        if len(night_data) != nsamples:
            print(f"ignored night data { night } len {len(night_data)}")
            continue 
        nights.append(night_data)
        nights_info.append([night.strftime("%m/%d"), night_data.index.time[0], night_data.index.time[-1], 
            np.sum(night_data.values), np.count_nonzero(night_data.values), night_data.size])
        msgs.append(f"day {nights_info[-1][0]} time {nights_info[-1][1]} {nights_info[-1][2]} sum_movs {nights_info[-1][3]:5.1f} event count {nights_info[-1][4]:3d} {nights_info[-1][5]}")
        if verbose:
            print(msgs[-1])    
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