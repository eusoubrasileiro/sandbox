import pandas as pd
import numpy as np
import datetime 
from matplotlib import pylab as plt
import datetime


def plot_nights(df, body_pixels, cam_name='frontwall', verbose=False, nights=1,
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
    dfp = df.resample('5T').sum() # resample 5 min, summing where there was no data it uses 0    
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
    series =  []    
    msgs = [] 
    params = []
    for night, night_data in dfp.groupby(dfp.night)['nchange_pixels']:     
        sp = night_data[ ( (night_data.index.time > datetime.time(hour=20)) & (night_data.index.time < datetime.time(hour=23, minute=59, second=59)) ) | 
            ( (night_data.index.time > datetime.time(hour=0)) & (night_data.index.time < datetime.time(hour=6)) ) ]
        if len(sp) == 0 or len(sp) != 118:
            print(f"ignored night data { night } len {len(sp)}")
            continue 
        series.append(sp)
        params.append([night.strftime("%m/%d"), sp.index.time[0], sp.index.time[-1], 
            np.sum(sp.values), np.count_nonzero(sp.values), sp.size])
        msgs.append(f"day {params[-1][0]} time {params[-1][1]} {params[-1][2]} sum_movs {params[-1][3]:5.1f} event count {params[-1][4]:3d} {params[-1][5]}")
        if verbose:
            print(msgs[-1])    
    # plot number of last nights defined
    fig, axis = plt.subplots(nights,1,figsize=(15,4*nights)) 
    last_nights = series[-nights:]     # latests nights 
    nights = [ param[0] for param in params[-nights:]]
    for i, sp in enumerate(last_nights):        
        axis[i].plot(sp.index.values, sp.values, linewidth=0.5, color='b', label='night of day '+nights[i]+' '+addtext)                             
        axis[i].fill_between(sp.index, sp.values, 0)
        axis[i].grid()
        axis[i].set_ylim(0, 100)        
        axis[i].set_ylabel('% Dancing Kid')  
        # We need to draw the canvas, otherwise the labels won't be positioned and 
        # won't have values yet.
        fig.canvas.draw()
        # remove date from tick labels
        ticks = [ t.get_text().split()[-1] for t in axis[i].get_xticklabels() ]
        axis[i].set_xticklabels(ticks)
        axis[i].legend(fontsize=18)
    if stacking: # stack to see any underline pattern        
        if 'selected' in stacking:
            series = last_nights 
        s0 = series[0].values.copy() 
        for night_data in series: # series[2:]:
            s0 += night_data.values
        fig, axis = plt.subplots(1,1,figsize=(15,4)) 
        s0 = s0/(len(series)-1)
        axis.plot(night_data.index, s0, color='b', linewidth=0.5, label='stacked nights')
        axis.set_ylim(min(s0), max(s0))
        axis.fill_between(night_data.index, s0, 0, color='k')
        axis.legend(fontsize=18)
        fig.canvas.draw()
        # remove date from tick labels
        ticks = [ t.get_text().split()[-1] for t in axis.get_xticklabels() ]
        axis.set_xticklabels(ticks)
        print("stacked ", len(series), " series")
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