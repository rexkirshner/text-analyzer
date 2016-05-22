#!/usr/bin/env python3 

import csv, collections, datetime, pprint, os, time

from collections import Counter
#from datetime import datetime
from bisect import bisect_left

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


synonyms = {
    'STOP':'Kit Evans'
}

def timestamp(dt):
    return (dt - datetime.date(1970, 1, 1)) / datetime.timedelta(seconds=1)

class History(object):
    
    def __init__(self, filename):
        self._sms_history = []
        self.participants = ["TBD"]
        self._participant_counter = Counter()
        self._filename = filename
        
    def load(self):
        with open(self._filename, 'r') as csvfile:
            msg_hist_reader = csv.reader(csvfile, delimiter=',')
            next(msg_hist_reader, None)
            for row in msg_hist_reader:
                name = synonyms[row[0].strip()] if row[0].strip() in synonyms else row[0].strip()
                self.append(datetime.datetime.strptime(row[3], "%b %d, %Y, %I:%M:%S %p"), [row[1], name])
                self._participant_counter[name] += 1
            self.participants = list(self._participant_counter.keys())
            self.participants.remove('Me')
        csvfile.close()

    def append(self, timestamp, message):
        self._sms_history += [(timestamp, message)]
        
    def getStats(self):
        participants =  ', '.join(self.participants)
        counts = ', '.join('{!s} = {!r}'.format(key,val) for (key,val) in self._participant_counter.items())
        return "The thread with %s has %d messages \r\n - Senders: %s" % (participants, len(self._sms_history), counts)
    
    def first(self):
        return self._sms_history[0]
    
    def last(self):
        return self._sms_history[-1]

    def search_item(self, item):
        high = len(self._sms_history)
        pos = bisect_left(self._sms_history, item, 0, high)
        return (pos if pos != high and self._sms_history[pos] == item else -1)
    
    def search_date_range(self, start, end):
        for i in range(0, len(self._sms_history)):
            if self._sms_history[i][0] >= start:
                i_start = i
                break
        
        for i in list(reversed(range(0, len(self._sms_history)))):
            if self._sms_history[i][0] <= end:
                i_end = i
                break
        
        return (i_start, i_end)
        
    def getHistory(self, start = -1):
        start = start if not start == -1 else len(self._sms_history)
        return self._sms_history[start:]
    
    def appendHistory(self, new_history):
        self._sms_history += (new_history)
        for message in new_history:
            self._participant_counter[message[1][1]] += 1
        return len(self._sms_history)      
    
    '''
    Takes two Histories and returns a new history with merged data. Returns none if participants do not match
    '''
    def merge(self, other_history):
        
        if len(set(self.participants).difference(other_history.participants)) > 0:
            return None
        
        if self.first()[0] < other_history.first()[0]:
            older = self
            newer = other_history
        else:
            older = other_history
            newer = self
        
        pos = newer.search_item(older.last())
        older.appendHistory(newer.getHistory(pos + 1))
        
        return older
    
    
    '''
    Done entirely while drunk, can definitely be optimized/rewritten to be much easier to read
    
    5/20/2016
    '''
    def histogram_data(self, resolution = 'month', combined = True, start = None, stop = None):
        s_date = start if start else self.start_date()
        e_date = stop if stop else self.end_date()

        s, e = self.search_date_range(s_date, e_date)
        flat_messages = {}
        if combined:
            flat_messages =  {'Combined':[timestamp(x[0].date()) for x in self._sms_history[s:e]]}
        else:
            for participant in self.participants + ['Me']:
                flat_messages[participant] = [timestamp(x[0].date()) for x in self._sms_history[s:e] if x[1][1] == participant]
        
        plt_data = []
        for history in flat_messages.items():
            label = history[0]
            mpl_data = mdates.epoch2num(history[1])
            plt_data += [(label, mpl_data)]   

        elapsed_time = e_date - s_date
        if  resolution == 'day':
            num_buckets = elapsed_time.days
        elif resolution == 'year':
            num_buckets = int(elapsed_time.days / 365) + 1
        else:
            num_buckets = int(elapsed_time.days / 30) + 1
        
        data_sets = []
        for person in plt_data:
            y, bin_edges = np.histogram(person[1], bins = num_buckets)
            bin_centers = 0.5*(bin_edges[1:]+bin_edges[:-1])

            data_sets.append((person[0], y, bin_centers))
            
        return data_sets

    def histogram_time_of_day(self, resolution = 'hour', combined = True, start = None, stop = None):
        s_date = start if start else self.start_date()
        e_date = stop if stop else self.end_date()

        s, e = self.search_date_range(s_date, e_date)
        
        days_of_week = [[] for x in range(7)]
        for message in self._sms_history[s:e]:

            time_of_day = message[0]
            
            if resolution == 'hour':
                num_buckets = 24
                days_of_week[time_of_day.weekday()] += [time_of_day.hour]

        
        data_sets = []
        for day in days_of_week:
            y, bin_edges = np.histogram(day, bins = num_buckets)
            bin_centers = 0.5*(bin_edges[1:]+bin_edges[:-1])
            data_sets.append((y, bin_centers))
        
        return data_sets
     
                
            
        
                    


    def start_date(self):
        if '_start' not in locals():
            self._start = self._sms_history[0][0]
        return self._start 
    
    def end_date(self):
        if '._end' not in locals():
            self._end = self._sms_history[-1][0]
        return self._end 
                


class Grapher(object):
    
    COLORS = ['red', 'blue', 'green']
    
    def __init__(self):
        self._curr_col_i = 0
        fig, ax = plt.subplots(1, 1)
        self.axes = [(ax,[])]
    
    def add_histograms(self, data_sets, **settings):
        for data in data_sets:
            self.add_histogram(data, settings)
    '''
    This probably needs a look too 
    
    -Drunk Rex    
    5/20/2016
    '''
    def add_histogram(self, data, settings):
        ax_and_data = self.axes[0]
        ax = ax_and_data[0]
        label, y, bin_centers = data

        chart_type = settings.get('chart_type', 'bar')
        
        resolution = settings.get('resolution', 'month')
        width = 5
        if  resolution == 'day':
            locator = mdates.DayLocator()
            formator = mdates.DateFormatter('%m-%d-%y')
        elif resolution == 'year':
            locator = mdates.YearLocator()
            formator = mdates.DateFormatter('%Y')
        else:
            locator = mdates.MonthLocator()
            formator = mdates.DateFormatter('%m-%y')
        
        if chart_type == 'line':
            ax.plot(bin_centers, y, '-', label = label, color = Grapher.COLORS[self._curr_col_i]) 
        elif chart_type == 'bar':
            print('start: %s end: %s' % (bin_centers[0], bin_centers[-1]))
            bottom = ax_and_data[1][-1] if len(ax_and_data[1]) >= 1 else None
            ax.bar(bin_centers, y, width = width, label = label, color = Grapher.COLORS[self._curr_col_i], bottom=bottom)
            print(type(ax))
        ax_and_data[1].append(y)
        self._curr_col_i += 1 
        
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formator)
        #ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
        print(ax.get_xlim())

        ax.legend()
        
        
    def graph(self, **settings):
        if settings.get('log_scale', False):
            plt.yscale('log', nonposy='clip')
        
        #fig = plt.figure()
        
        
        plt.show()

def consolidate_history(name):
    history = None
    for f in os.listdir(os.path.join(os.getcwd(), 'messages', name)):
        next_hist = History(os.path.join(os.getcwd(), 'messages', name, f))            
        next_hist.load()
        if history != None:
            history = history.merge(next_hist)
        else:
            history = next_hist
    return history

if __name__ == '__main__':

    messsage_to_sober_rex = '''
        -When you graph by year the bar charts are to the right of the ticks, but not in the middle. Why?
        --Probably true when you graph by month and day but they are too close together
        -Speaking of day, why does it error? Is it too many points to graph?
        --check what happens when you try to line graph on day... something weird happens that doesn't happen on bar
        --never mind, that was stupid... i wrote list instead of line in the options. Same error for bar and line chart
        I just got distracted by tinder
        -check your work, I feel like everything I did could be written in 1/5 of the lines 
        
        -Figure out how to put a line chart and a bar chart on the same graph
        -I'm pretty sure you are going to have to create the full list of x values and populate with y values
        --I have no idea how np.histogram works but I think it just creates values in the buckets where the bucket value is greater than 0
        ---actually now that I think about it, that wouldn't make sense because it just returns bucket sizes, not a list of x values
        ----go check wtf bin_edges is. Is it a list? and what is bin_centers, a list? figuring that out will probably answer this question
        --either way you are going to have to figure out how to graph two sets of texts given you cant assume you texted both people on the same bucket (day/month/year)
        
        -WTF are subplots? How does that work?
        --If I want to put all data on one graph how do I do that without fucking it up?
        ---When do you set the axis?
        ----If the data has different axis, does pyplot figure that out or do you have to massage it first?
        ---If I want to do on graph on top and a bunch below how do I do that?
        ----I'm thinking total on top, one for each day, texts per time of day for each day below
        
        ALL OF THIS IS JUST GRAPHING IS THAT ANALYTICS?
        
        I'm pretty sure you're going to be embarrassed you wrote this and not read it
    '''
    
    #print(messsage_to_sober_rex)
    
    #exit(0)

    print('\r\n\r\n')  
    print('-----------------------------------------')
    kit_history = consolidate_history('Kit')
    
    #a = History('messages/test files/test1.csv')
    #a.load()
    
    data_sets = kit_history.histogram_time_of_day()
    fig, ax = plt.subplots(1, len(data_sets))
    
    for i, data in enumerate(data_sets):
        y, bin_centers = data
        ax[i].bar(bin_centers, y)
    plt.show()

    
    
    
    #brett_history = consolidate_history('Brett')
    
    #print()
    
    #g = Grapher()
    
    #resolution = 'month'
    
    #data = kit_history.histogram_data(resolution = resolution, combined = False, start = None, stop = None)
    #g.add_histograms(data, resolution = resolution, chart_type = 'bar')
    
    #data = brett_history.histogram_data(resolution = resolution, combined = True, start = None, stop = None)
    #g.add_histograms(data, resolution = resolution, chart_type = 'line')
          
    #g.graph(log_scale=True)
    
    
    
    print('-----------------------------------------')
    print('\r\n\r\n')  
    
    
    
    
    
    
    
    
    
    
    