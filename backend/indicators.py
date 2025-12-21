import pandas as pd
from content import source
from zoneinfo import ZoneInfo
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, datetime, timezone
from matplotlib.figure import Figure

plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams.update({'font.size': 8})

#Function to convert date to UTC unix timestamp
def date_convert_in(date_str:str):
    dt_est = datetime.fromisoformat(date_str)
    dt_est = dt_est.replace(tzinfo=ZoneInfo("America/New_York"))
    dt_utc = dt_est.astimezone(ZoneInfo("UTC"))
    unix_timestamp = int(dt_utc.timestamp())
    print(dt_utc.strftime("%Y-%m-%d %H:%M:%S.%f"), unix_timestamp)
    return unix_timestamp

#Function to convert UTC unix timestamp into EST datetime format
def date_convert_out(unix_timestamp: int):
    dt_utc = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))
   
    return pd.to_datetime(dt_est)

def get_series(symbol, from_date='2025-01-01'):
    obj = source.EODData()
    resp = obj.historical([symbol], from_date=from_date)[symbol]
    frame = pd.DataFrame(resp)
    return frame 


class VolSpread:

    def __init__(self, symbol, from_date='2022-05-16 00:00'):
        self.symbol = symbol
        self.upper = 0.8
        self.lower =0.7
        self.from_date = from_date
        self.to_date = datetime.now()
        self.start_time = '09:30'
        self.end_time = '16:00'
        self.raw_data = None


    def get_data_part(self, from_date, to_date):
        obj = source.EODData()
        from_date = date_convert_in(from_date)
        now_str = to_date
        to_date = date_convert_in(now_str)
        data = obj.intraday([self.symbol], interval="1m" ,from_date=from_date, to=to_date)
        frame = pd.DataFrame(data)
        frame['datetime'] = [date_convert_out(x) for x in frame.timestamp]
        frame.set_index('datetime', inplace=True)
        return frame[['close','open', 'high', 'low', 'volume']]
      
    def get_data(self, max_req=100):
        from_date = self.from_date
        to_date = self.to_date
        intervals = pd.date_range(start=from_date, end=to_date, freq=f'{max_req}D')
        intervals = intervals.to_list()
        intervals = [x.strftime("%Y-%m-%d %H:%M:%S.%f") for x in intervals]
        intervals.append(to_date.strftime("%Y-%m-%d %H:%M:%S.%f"))
        data_lis = []
        

        for date_init, date_end in zip(intervals, intervals[1:]):
            data = self.get_data_part(date_init, date_end)
            data_lis.append(data)
        
        all_data = pd.concat(data_lis)
        all_data['returns'] = all_data['close'].pct_change()
        self.raw_data = all_data
        return all_data

    def actual_vol(self):
        if self.raw_data is not None:
            data = self.raw_data.copy()
        else:
            data = self.get_data()

        data['date'] = data.index
        data = data.between_time(self.start_time, self.end_time)
        vol =  data.resample('D').agg({'returns':'std', 'date':'count', 'close':'last', 'volume':'sum'})
        vol.dropna(inplace=True)

        vol['ann_vol'] = (vol['returns'] * np.sqrt(252*vol['date']))*100
        vol.index = vol.index.tz_localize(None)

        self.vol_data = vol

        return vol
    
    def vix_vol(self):
        vix_data = get_series('VIX1D.INDX', from_date = self.from_date)
        vix_data.set_index('date', inplace=True)
        vix_data.index = pd.to_datetime(vix_data.index)
        self.vix_data = vix_data
        return vix_data
    
    def indicator(self):
        actual_vol = self.actual_vol()
        vix_data = self.vix_vol()

        all_data = actual_vol.merge(vix_data[['close']], left_index=True, right_index=True, how='left', suffixes=('', '_VIX'))
        all_data = all_data[['close', 'volume', 'ann_vol', 'close_VIX']]
        all_data.columns = ['close', 'volume', 'actual_vol', 'vix_vol']
        all_data['vol_ratio'] = all_data['actual_vol'] / all_data['vix_vol']
        all_data['ratio_avg'] = all_data['vol_ratio'].rolling(window=5).mean()
        all_data.loc[all_data['ratio_avg']>self.upper, 'signal'] = -1
        all_data.loc[all_data['ratio_avg']<self.lower, 'signal'] = 0
        all_data['signal'] = all_data['signal'].fillna(1)

        self.indicator_data = all_data

        return all_data

    def plot_indicator(self):
        if hasattr(self, 'indicator_data'):
            all_data = self.indicator_data
        else:
            all_data = self.indicator()

        fig, (ax1, ax4, ax3) = plt.subplots(3,1,figsize=(12, 8), gridspec_kw={'height_ratios': [3, 0.5,1]})
        ax1.set_title('SPY Actual Volatility vs VIX 1 Day Index')
        ax1.plot(all_data['actual_vol'], label='Actual Volatility', alpha=0.5)
        ax1.plot(all_data['vix_vol'], label='1 Day VIX Index', color='green', alpha=0.5)

        ax2 = ax1.twinx()
        ax2.plot(all_data['close'], color='blue', label='S&P 500 (SPY)')

        ax4.fill_between(all_data.index, 1, color='yellow', alpha=0.5, where=all_data['signal']==1)
        ax4.fill_between(all_data.index, 1, color='green', alpha=0.5, where=all_data['signal']==0)
        ax4.fill_between(all_data.index, 1, color='red', alpha=0.5, where=all_data['signal']==-1)



        ax3.plot(all_data['vol_ratio'], color='purple', label='Volatility Ratio (Actual/VIX)', alpha=0.5)
        ax3.plot(all_data['ratio_avg'], color='red', label='5-Day Avg of Volatility Ratio')
        ax3.plot(all_data.index, np.repeat(self.lower, len(all_data.index)), color='black', linestyle='--')
        ax3.plot(all_data.index, np.repeat(self.upper, len(all_data.index)), color='black', linestyle='--')
        ax2.grid(False)
        ax1.grid(False)
        ax3.grid(False)

        fig.legend(loc='lower center', ncol=3)

        return fig

class VixSpread:
    def __init__(self, from_date='2022-05-16 00:00'):
        
        self.from_date = from_date
        self.raw_data = None
        self.upper = 12
        self.lower = 8
        self.avg_window = 5
    
    def get_spy_data(self):
        spy_data = get_series('SPY', from_date = self.from_date)
        spy_data.set_index('date', inplace=True)
        spy_data.index = pd.to_datetime(spy_data.index)
        self.spy_data = spy_data
        return spy_data
    
    def get_vix_data(self):
        vix_data = get_series('VIX.INDX', from_date = self.from_date)
        vix_data.set_index('date', inplace=True)
        vix_data.index = pd.to_datetime(vix_data.index)
        self.vix_data = vix_data
        return vix_data

    def get_vvix_data(self):
        vvix_data = get_series('VVIX.INDX', from_date = self.from_date)
        vvix_data.set_index('date', inplace=True)
        vvix_data.index = pd.to_datetime(vvix_data.index)
        self.vvix_data = vvix_data
        return vvix_data
    
    def indicator(self):
        vix_data = self.get_vix_data()
        vvix_data = self.get_vvix_data()
        spy_data = self.get_spy_data()

        all_data = vix_data.merge(vvix_data[['close']], left_index=True, right_index=True, how='left', suffixes=('_VIX', '_VVIX'))
        all_data = all_data.merge(spy_data[['close']], left_index=True, right_index=True, how='left')

        all_data['vvix_vix_diff'] = all_data['close_VVIX'] / all_data['close_VIX']
        all_data['dif_avg'] = all_data['vvix_vix_diff'].rolling(window=self.avg_window).mean()

        all_data.loc[all_data['dif_avg']>self.upper, 'signal'] = -1
        all_data.loc[all_data['dif_avg']<self.lower, 'signal'] = 0
        all_data['signal'] = all_data['signal'].fillna(1)

        self.indicator_data = all_data


        return all_data
    

    def plot_indicator(self):
        
        all_data = self.indicator().dropna()
        
        # --- ADJUSTMENT 1: Use Figure() instead of plt ---
        # We create the Figure object explicitly.
        fig = Figure(figsize=(12, 10))
    
        # --- ADJUSTMENT 2: Use the fig instance to create subplots ---
        # This keeps the axes "owned" by this specific figure only.
        (ax1, ax2, ax3) = fig.subplots(3, 1, gridspec_kw={'height_ratios': [3, 0.5, 1]})

        ax1.set_title('VIX and VVIX with S&P500 Price', fontsize=8)
        ax1.plot(all_data['close_VVIX'], color='green', alpha=0.5, label='VVIX')
        ax1.plot(all_data['close_VIX'], color='blue', alpha=0.5, label='VIX')

        ax4 = ax1.twinx()
        ax4.plot(all_data['close'], color='blue', label='S&P500 (SPY)')

        ax2.fill_between(all_data.index, 1, color='yellow', alpha=0.5, where=all_data['signal']==1)
        ax2.fill_between(all_data.index, 1, color='green', alpha=0.5, where=all_data['signal']==0)
        ax2.fill_between(all_data.index, 1, color='red', alpha=0.5, where=all_data['signal']==-1)

        ax3.plot(all_data['vvix_vix_diff'], color='orange', label='VVIX - VIX', alpha=0.7)
        ax3.plot(all_data['dif_avg'], color='red', label='5-Day Avg of VVIX - VIX', alpha=0.7)
        ax3.plot(all_data.index, np.repeat(self.lower, len(all_data.index)), color='black', linestyle='--')
        ax3.plot(all_data.index, np.repeat(self.upper, len(all_data.index)), color='black', linestyle='--')
        ax1.grid(False)
        ax2.grid(False)
        ax4.grid(False)
        ax3.grid(False)
        fig.legend(loc='lower center', ncol=6)

        return fig