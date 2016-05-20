#!/usr/bin/env python3 

import csv, collections, datetime, pprint, os

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
    
    def histogram_data(self, resolution = 'month', combined = True, start = None, stop = None):
        s_date = start if start else self.start_date()
        e_date = stop if stop else self.end_date()

        s, e = self.search_date_range(s_date, e_date)
        flat_messages = {}
        if combined:
            flat_messages =  {'combined':[timestamp(x[0].date()) for x in self._sms_history[s:e]]}
        else:
            for participant in self.participants + ['Me']:
                flat_messages[participant] = [timestamp(x[0].date()) for x in self._sms_history[s:e] if x[1][1] == participant]
        
        plt_data = []
        for history in flat_messages.items():
            mpl_data = mdates.epoch2num(history[1])
            plt_data += [mpl_data]   

        elapsed_time = e_date - s_date
        if  resolution == 'day':
            num_buckets = elapsed_time.days
            locator = mdates.DayLocator()
            formator = mdates.DateFormatter('%m-%d-%y')
        elif resolution == 'year':
            num_buckets = int(elapsed_time.days / 365) + 1
            locator = mdates.YearLocator()
            formator = mdates.DateFormatter('%Y')
        else:
            num_buckets = int(elapsed_time.days / 30) + 1
            locator = mdates.MonthLocator()
            formator = mdates.DateFormatter('%m-%y')
        
        y, bin_edges = np.histogram(plt_data, bins = num_buckets)
        bin_centers = 0.5*(bin_edges[1:]+bin_edges[:-1])
        
        return (y, bin_edges, bin_centers)

    
   
    def start_date(self):
        if '_start' not in locals():
            self._start = self._sms_history[0][0]
        return self._start 
    
    def end_date(self):
        if '._end' not in locals():
            self._end = self._sms_history[-1][0]
        return self._end 
                


class Grapher(object):
    
    def __init__(self):
        self._data_sets = {}
        pass
    
    def add_histogram(self, data):
        fig, ax = plt.subplots(1,1)
        
        y, bin_edges, bin_centers = data
        
        
        ax.plot(bin_centers, y, '-') 
                
        self._data_sets.append(ax)
        
        
    
    def graph(self, **settings):
        ax = self._data_sets[0]
        resolution = settings.get('resolution', 'month')

        if  resolution == 'day':
            locator = mdates.DayLocator()
            formator = mdates.DateFormatter('%m-%d-%y')
        elif resolution == 'year':
            locator = mdates.YearLocator()
            formator = mdates.DateFormatter('%Y')
        else:
            locator = mdates.MonthLocator()
            formator = mdates.DateFormatter('%m-%y')
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formator)
        ax.legend()
        if settings.get('log_scale', False):
            plt.yscale('log', nonposy='clip')

        
        plt.show()
    

if __name__ == '__main__':

    print('\r\n\r\n')  
    print('-----------------------------------------')
    kit_history = None
    for f in os.listdir(os.path.join(os.getcwd(), 'messages/Kit')):
        next_hist = History(os.path.join(os.getcwd(), 'messages/Kit', f))            
        next_hist.load()
        if kit_history != None:
            kit_history = kit_history.merge(next_hist)
        else:
            kit_history = next_hist
    print(kit_history.getStats())
    
    print()
    
    g = Grapher()

    g.add_histogram(kit_history.histogram_data(resolution = 'month', combined = True, start = None, stop = None))
          
    g.graph(resolution='month')
    
    
    
    print('-----------------------------------------')
    print('\r\n\r\n')  
    
    
    
    
    
    
    
    
    
    
    