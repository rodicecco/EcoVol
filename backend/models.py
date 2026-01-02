import pandas as pd
from content import source
from zoneinfo import ZoneInfo
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, datetime, timezone
from matplotlib.figure import Figure
from content import admin

plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams.update({'font.size': 8})


#-1 means red light
#1 means green light
#0 means yellow light

#Class to gather data necessary to run all models
class Data:

    def __init__(self, from_date='2022-05-16 00:00', benchmark='SPY'):
        #Initial date for loading data
        self.from_date = from_date
        self.benchmark = benchmark

    def check_data(self):
        if hasattr(self, 'data'):
            return True
        else:
            return False
    
    #Pull raw historical data from loaded database
    def get_historical(self, symbol, driver='close', append=True):

        with admin.Database('', []).engine().connect() as conn:
            query = f'''SELECT date, {driver} FROM historical WHERE symbol = '{symbol}' 
                        AND date > '{self.from_date}';'''
            data = pd.read_sql(query, conn)
        
        data.set_index('date', inplace=True)
        data.index = pd.to_datetime(data.index)
        data = data[[driver]]
        data.columns = [symbol]

        if append is True:
            if self.check_data() is True:
                if symbol not in self.data.columns:
                    self.data = self.data.merge(data, how='left', left_index=True, right_index=True)
            else:
                self.data = data

        return data

    #Calculated historical volatility
    def volatility(self, symbol='SPY', start_time='09:30', end_time='16:00', append=True):
        name = 'ACTVOL'

        query = f'''SELECT datetime, close FROM intraday WHERE symbol ='{symbol}'
                    AND datetime > '{self.from_date}';'''
        
        with admin.Database('', []).engine().connect() as conn:
            data = pd.read_sql(query, conn)

        data['returns'] = data['close'].pct_change()
        data.set_index('datetime', inplace=True)

        data['date'] = data.index
        data = data.between_time(start_time, end_time)
        volatility = data.resample('D').agg({'returns':'std', 'date':'count', 'close':'last'})
        volatility.dropna(inplace=True)
        volatility[name] = (volatility['returns'] * np.sqrt(252*volatility['date']))*100
        volatility.index = volatility.index.tz_localize(None)

        volatility = volatility[[name]]

        if append is True:
            if self.check_data() is True:
                if name not in self.data.columns:
                    self.data = self.data.merge(volatility, how='left', left_index=True, right_index=True)
            else:
                self.data = volatility

        return volatility
    
    def load_data(self):
        self.get_historical(self.benchmark)
        self.get_historical('VIX.INDX')
        self.get_historical('VVIX.INDX')
        self.get_historical('VIX1D.INDX')
        self.volatility()
        return True


#Model administration class
class ModelAdmin:

    def __init__(self):
        pass

        #Plot parameters
        self.view_ratios = [2, 0.5, 0.5]
    
    def api(self):
        if hasattr(self, 'model_data'):
            data = self.model_data
        else:
            data = self.indicator()

        api_data = {'name': self.name, 
                    'description': self.description, 
                    'data': data.reset_index().to_dict()}
        
        return api_data

    def plot_indicator(self, from_date=None):

        if hasattr(self, 'model_data'):
            data = self.model_data
        else:
            data = self.indicator()

        if from_date is not None:
            from_date = from_date
        else:
            from_date = self.from_date

        data = self.model_data.loc[from_date:]
        fig = Figure(figsize=(12, 6))
        axes = fig.subplots(nrows=3, ncols=1, sharex=True, gridspec_kw={'height_ratios': self.view_ratios})

        main_ax = axes[0]
        main_ax.set_title(self.name)
        for col in self.axis[0]:
            main_ax.plot(data.index, data[col], label=col)
        main_ax.grid(False)

        sec_main_ax = axes[0].twinx()
        for col in self.axis[1]:
            sec_main_ax.plot(data.index, data[col], label=col, alpha=0.5)
        sec_main_ax.grid(False)

        light_ax = axes[1]
        light_ax.fill_between(data.index, 1, color='yellow', alpha=0.5, where=data['SIGNAL']==self.other)
        light_ax.fill_between(data.index, 1, color='green', alpha=0.5, where=data['SIGNAL']==self.above_up)
        light_ax.fill_between(data.index, 1, color='red', alpha=0.5, where=data['SIGNAL']==self.below_low)
        light_ax.grid(False)

        supp_ax = axes[2]
        for col in self.axis[2]:
            supp_ax.plot(data.index, data[col], label=col)
        supp_ax.plot(data.index, [self.upper]*len(data), label='Upper Threshold', color='black', linestyle='--')
        supp_ax.plot(data.index, [self.lower]*len(data), label='Lower Threshold', color='black', linestyle='--')
        supp_ax.grid(False)

        fig.tight_layout()

        return fig





#Composite model class
class Composite(ModelAdmin):
    def __init__(self, models:list, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'Composite Traffic Light'
        self.code = 'COMPOSITE'
        self.description = '''Composite model based on aggregate of signals'''
        self.from_date = from_date

        #Data and model parameters
        self.benchmark = benchmark
        self.upper = 2
        self.lower = 1
        self.above_up = -1
        self.below_low = 1
        self.other = 0

        #Available models
        self.data_obj = Data(benchmark=self.benchmark)
        self.models_list = models
        self.models = {}

        ModelAdmin.__init__(self)

        self.data_obj.load_data()

    def load_models(self):

        for model in self.models_list:
            obj = model(self.data_obj.data, benchmark=self.benchmark, from_date=self.from_date)
            obj.indicator()
            self.models[obj.code] = obj

            if hasattr(self, 'signal_data'):
                self.signal_data = self.signal_data.merge(obj.signal, how='left', left_index=True, right_index=True)
            else:
                self.signal_data = obj.signal
        
        return self.signal_data
    
    def refresh_models(self):

        if hasattr(self, 'signal_data'):
            delattr(self, 'signal_data')

        for model in self.models:
            obj = self.models[model]
            obj.indicator()
            if hasattr(self, 'signal_data'):
                self.signal_data = self.signal_data.merge(obj.signal, how='left', left_index=True, right_index=True)
            else:
                self.signal_data = obj.signal
        
        return self.signal_data
    
    def indicator(self):
        if hasattr(self, 'signal_data'):
            data = self.refresh_models()
        else:
            data = self.load_models()
        
        data['SUMCOMP'] = data.sum(axis=1)
        data = data[['SUMCOMP']]
        comp_data = self.data_obj.data[[self.benchmark]]
        data = data.merge(comp_data, how='left', left_index=True, right_index=True)
        data.columns = [self.code, self.benchmark]

        data.loc[data[self.code]>self.upper, 'SIGNAL'] = self.above_up
        data.loc[data[self.code]<self.lower, 'SIGNAL'] = self.below_low
        data['SIGNAL'] = data['SIGNAL'].fillna(self.other)


        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:[], 
                     2:[self.code]}

        return data
    
    def master_api(self):

        if hasattr(self, 'model_data'):
            data = self.model_data
        else:
            data = self.indicator()

        api_data = {self.code:self.api()}

        for model in self.models:
            api_data[model] = self.models[model].api()

        return api_data


        

class VolSpread(ModelAdmin):
    def __init__(self, data, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'Volatility Spread'
        self.code = 'VOLSPREAD'
        self.description = '''Spread between realized daily volatility on 1-min intervals and the 1-day VIX index'''
        self.from_date = from_date   
        
        #Data and model parameters
        self.benchmark = benchmark
        self.data = data
        self.upper = 0.8
        self.lower = 0.7
        self.avg_window = 5
        self.above_up = -1
        self.below_low = 1
        self.other = 0
        
        ModelAdmin.__init__(self)
    
    def indicator(self):

        data = self.data.copy()[[self.benchmark, 'ACTVOL', 'VIX1D.INDX']]
        data['VOLRATIO'] = data['ACTVOL'] / data['VIX1D.INDX']
        data['AVGRATIO'] = data['VOLRATIO'].rolling(window=self.avg_window).mean()

        data.loc[data['AVGRATIO']>self.upper, 'SIGNAL'] = self.above_up
        data.loc[data['AVGRATIO']<self.lower, 'SIGNAL'] = self.below_low
        data['SIGNAL'] = data['SIGNAL'].fillna(self.other)
        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:['ACTVOL', 'VIX1D.INDX'], 
                     2:['VOLRATIO', 'AVGRATIO']}
        return data

class VolAutocorr(ModelAdmin):
    def __init__(self, data, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'Volatility Autocorrelation'
        self.code = 'VOLAUTOCORR'
        self.description = '''Autocorrelation of realized daily volatility on 1-min intervals'''
        self.from_date = from_date   
        
        #Data and model parameters
        self.benchmark = benchmark
        self.data = data
        self.upper = 0.15
        self.lower = 0.0
        self.lag = 10
        self.above_up = -1
        self.below_low = 1
        self.other = 0
        
        ModelAdmin.__init__(self)
    
    def indicator(self):

        data = self.data.copy()[[self.benchmark,'ACTVOL']]
        data['AUTOCORR'] = data['ACTVOL'].rolling(window=self.lag).apply(lambda x: x.autocorr(lag=1))

        data.loc[data['AUTOCORR']>self.upper, 'SIGNAL'] = self.above_up
        data.loc[data['AUTOCORR']<self.lower, 'SIGNAL'] = self.below_low
        data['SIGNAL'] = data['SIGNAL'].fillna(self.other)
        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:['ACTVOL'], 
                     2:['AUTOCORR']}

        return data


class VixSpread(ModelAdmin):
    def __init__(self, data, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'VIX - VVIX Spread'
        self.code = 'VIXVVIX'
        self.description = '''Spread between VVIX and VIX index'''
        self.from_date = from_date   
        
        #Data and model parameters
        self.benchmark = benchmark
        self.data = data
        self.upper = 12
        self.lower = 8
        self.avg_window = 5
        self.above_up = -1
        self.below_low = 1
        self.other = 0
        
        ModelAdmin.__init__(self)
    
    def indicator(self):

        data = self.data.copy()[[self.benchmark,'VIX.INDX', 'VVIX.INDX']]
        data['VIXDIF'] = data['VVIX.INDX'] - data['VIX.INDX']
        data['AVGDIF'] = data['VIXDIF'].rolling(window=self.avg_window).mean()


        data.loc[data['AVGDIF']>self.upper, 'SIGNAL'] = self.above_up
        data.loc[data['AVGDIF']<self.lower, 'SIGNAL'] = self.below_low
        data['SIGNAL'] = data['SIGNAL'].fillna(self.other)
        
        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:['VVIX.INDX', 'VIX.INDX'], 
                     2:['VIXDIF', 'AVGDIF']}

        return data    