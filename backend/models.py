import pandas as pd
from content import source
from zoneinfo import ZoneInfo
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, datetime, timezone
from matplotlib.figure import Figure
from content import admin
import plotly.graph_objects as go
from plotly.subplots import make_subplots



plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams.update({'font.size': 8})


#-1 means red light
#1 means green light
#0 means yellow light

#Class to gather data necessary to run all models
class Data:

    def __init__(self, from_date='2022-05-16 00:00', benchmark='GSPC.INDX'):
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
                        AND date > '{self.from_date}'
                        ORDER BY date;'''
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
    
    def get_gex(self, append=True):
        symbol='gex'
        with admin.Database('', []).engine().connect() as conn:
            query = f'''SELECT date, {symbol} FROM dix WHERE date > '{self.from_date}';'''
            data = pd.read_sql(query, conn)
        
        data.set_index('date', inplace=True)
        data.index = pd.to_datetime(data.index)
        data = data[[symbol]]
        data.columns = [symbol]

        if append is True:
            if self.check_data() is True:
                if symbol not in self.data.columns:
                    self.data = self.data.merge(data, how='left', left_index=True, right_index=True)
            else:
                self.data = data

        return data

    
    def load_data(self):
        self.get_historical(self.benchmark)
        self.get_historical('VIX.INDX')
        self.get_historical('VVIX.INDX')
        self.get_historical('VIX1D.INDX')
        self.get_historical('SKEW.INDX')
        self.get_historical('VIX9D.INDX')
        self.get_historical('VIX3M.INDX')
        self.volatility()
        self.get_gex()
        return True


#Model administration class
class ModelAdmin:

    def __init__(self):
        pass

        #Plot parameters
        self.view_ratios = [2, 0.5, 0.5]
        self.color_map = {-1:'red', 1:'green', 0:'yellow'}
    
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
        light_ax.fill_between(data.index, 1, color=self.color_map[self.other], alpha=0.5, where=data['SIGNAL']==self.other)
        light_ax.fill_between(data.index, 1, color=self.color_map[self.above_up], alpha=0.5, where=data['SIGNAL']==self.above_up)
        light_ax.fill_between(data.index, 1, color=self.color_map[self.below_low], alpha=0.5, where=data['SIGNAL']==self.below_low)
        light_ax.grid(False)

        supp_ax = axes[2]
        for col in self.axis[2]:
            supp_ax.plot(data.index, data[col], label=col)
        supp_ax.plot(data.index, [self.upper]*len(data), label='Upper Threshold', color='black', linestyle='--')
        supp_ax.plot(data.index, [self.lower]*len(data), label='Lower Threshold', color='black', linestyle='--')
        supp_ax.grid(False)

        fig.tight_layout()

        return fig


    def plot_indicator_plotly(self, from_date=None):

        if hasattr(self, 'model_data'):
            data = self.model_data
        else:
            data = self.indicator()

        if from_date is not None:
            from_date = from_date
        else:
            from_date = self.from_date

        data = self.model_data.loc[from_date:]

        #Create subplots
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.05, 
            row_heights=self.view_ratios, 
            specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": False}]]
        )

        #Main axis (Row 1, Primary Y)
        for col in self.axis[0]:
            fig.add_trace(
                go.Scatter(x=data.index, y=data[col], name=col), 
                row=1, 
                col=1
            )
        
        #Seconday Main Axis (Row1, Secondary Y)
        for col in self.axis[1]:
            fig.add_trace(
                go.Scatter(x=data.index, y=data[col], name=col, opacity=0.5), 
                row=1, 
                col=1, 
                secondary_y=True
            )

        #Light axis
        color_map = {self.other: self.color_map[self.other], self.above_up: self.color_map[self.above_up], self.below_low: self.color_map[self.below_low]}
        bar_colors = [color_map.get(x, 'yellow') for x in data['SIGNAL']]

        fig.add_trace(
            go.Bar(
                x=data.index,
                y=[1] * len(data),
                marker_color=bar_colors,
                showlegend=False,
                marker_line_width=0
            ),
            row=2,
            col=1
        )
        
        #Support axis
        for col in self.axis[2]:
            fig.add_trace(
                go.Scatter(x=data.index, y=data[col], name=col), 
                row=3, 
                col=1
            )

        # Threshold lines
        fig.add_hline(y=self.upper, line_dash="dash", line_color="black", row=3, col=1)
        fig.add_hline(y=self.lower, line_dash="dash", line_color="black", row=3, col=1)

        # 5. Layout Styling
        fig.update_layout(
            title=self.name,
            height=800, # Adjust based on preference
            template="plotly_white",
            hovermode="x unified",
            showlegend=True,
            bargap=0
        )

        return fig
    
    def to_dict(self):
        dic = {}
        for param in self.params:
            dic[param] = getattr(self, param)
        return dic

    def from_dict(self, dic):
        for key, value in dic.items():
            setattr(self, key, value)
        return self


#Composite model class
class Composite(ModelAdmin):
    def __init__(self, models:list, data, benchmark='GSPC.INDX', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'Composite Traffic Light'
        self.code = 'COMPOSITE'
        self.description = '''Composite model based on aggregate of signals'''
        self.from_date = from_date
        self.status = 'Not Loaded'
        self.params = ['upper', 'lower', 'above_up', 'below_low']

        #Data and model parameters
        self.benchmark = benchmark
        self.upper = 2
        self.lower = 1
        self.above_up = -1
        self.below_low = 1
        self.other = 0

        #Available models
        self.data_obj = data
        self.models_list = models
        self.models = {}

        ModelAdmin.__init__(self)



    def load_models(self):
        #self.data_obj.load_data()
        if self.status == 'Not Loaded':

            for model in self.models_list:
                obj = model(self.data_obj, benchmark=self.benchmark, from_date=self.from_date)
                obj.indicator()
                self.models[obj.code] = obj

                if hasattr(self, 'signal_data'):
                    self.signal_data = self.signal_data.merge(obj.signal, how='left', left_index=True, right_index=True)
                else:
                    self.signal_data = obj.signal
            
            self.status = 'Loaded'
            return self.signal_data
        else:
            return self.signal_data

    
    def refresh_models(self):
        #self.data_obj.load_data()
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
        comp_data = self.data_obj[[self.benchmark]]
        data = data.merge(comp_data, how='left', left_index=True, right_index=True)
        data.columns = [self.code, self.benchmark]

        data.loc[data[self.code]>self.upper, 'SIGNAL'] = self.above_up
        data.loc[data[self.code]<self.lower, 'SIGNAL'] = self.below_low
        data['SIGNAL'] = data['SIGNAL'].fillna(self.other)
        data = data.dropna()

        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:[], 
                     2:[self.code]}
        
        self.last_stats = data.iloc[-1]
        self.last_update = data.index[-1]
        

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
    
    def to_dict(self):
        dic={}
        for param in self.params:
            dic[param] = getattr(self, param)
        dic['models'] = {name: model.to_dict() for name, model in self.models.items()}

        return dic
    
    def from_dict(self, dic):
        for param in self.params:
            setattr(self, param, dic[param])
        
        model_data = dic.get('models', {})
        for name, model_dict in model_data.items():
            self.models[name].from_dict(model_dict)
        
        return self


        

class VolSpread(ModelAdmin):
    def __init__(self, data, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'Volatility Spread'
        self.code = 'VOLSPREAD'
        self.description = '''Spread between realized daily volatility on 1-min intervals and the 1-day VIX index'''
        self.from_date = from_date   
        self.params = ['upper', 'lower', 'avg_window', 'above_up', 'below_low']

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
        data = data.dropna()
        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:['ACTVOL', 'VIX1D.INDX'], 
                     2:['VOLRATIO', 'AVGRATIO']}
        
        self.last_stats = data.iloc[-1]
        self.last_update = data.index[-1]
        return data

class VolAutocorr(ModelAdmin):
    def __init__(self, data, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'Volatility Autocorrelation'
        self.code = 'VOLAUTOCORR'
        self.description = '''Autocorrelation of realized daily volatility on 1-min intervals'''
        self.from_date = from_date
        self.params = ['upper', 'lower', 'lag', 'above_up', 'below_low']
        
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
        #Autocorrelation with last observation over a self.lag period
        data = self.data.copy()[[self.benchmark,'ACTVOL']]
        data['AUTOCORR'] = data['ACTVOL'].rolling(window=self.lag).apply(lambda x: x.autocorr(lag=1))

        data.loc[data['AUTOCORR']>self.upper, 'SIGNAL'] = self.above_up
        data.loc[data['AUTOCORR']<self.lower, 'SIGNAL'] = self.below_low
        data['SIGNAL'] = data['SIGNAL'].fillna(self.other)
        data = data.dropna()
        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:['ACTVOL'], 
                     2:['AUTOCORR']}
        
        self.last_stats = data.iloc[-1]
        self.last_update = data.index[-1]
        return data


class VixSpread(ModelAdmin):
    def __init__(self, data, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'VIX - VVIX Spread'
        self.code = 'VIXVVIX'
        self.description = '''Spread between VVIX and VIX index'''
        self.from_date = from_date
        self.params = ['upper', 'lower', 'avg_window', 'above_up', 'below_low']   
        
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
        data = data.dropna()
        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:['VVIX.INDX', 'VIX.INDX'], 
                     2:['VIXDIF', 'AVGDIF']}

        self.last_stats = data.iloc[-1]
        self.last_update = data.index[-1]
        return data
    

class GEX(ModelAdmin):
    def __init__(self, data, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'GEX'
        self.code = 'GEX'
        self.description = '''Gamma Exposure'''
        self.from_date = from_date   
        self.params = ['upper', 'lower', 'above_up', 'below_low']

        #Data and model parameters
        self.benchmark = benchmark
        self.data = data
        self.upper = 0
        self.lower = 0


        self.above_up = -1
        self.below_low = 1
        self.other = 0
        
        ModelAdmin.__init__(self)
    
    def indicator(self):

        data = self.data.copy()[[self.benchmark,'gex']]
        data.columns = [self.benchmark, self.code]

        data.loc[data[self.code]>self.upper, 'SIGNAL'] = self.above_up
        data.loc[data[self.code]<self.lower, 'SIGNAL'] = self.below_low
        data['SIGNAL'] = data['SIGNAL'].fillna(self.other)
        data = data.dropna()
        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:['GEX'], 
                     2:['GEX']}

        self.last_stats = data.iloc[-1]
        self.last_update = data.index[-1]
        return data
    

class Skew(ModelAdmin):
    def __init__(self, data, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'SKEW'
        self.code = 'SKEW'
        self.description = '''Volatility Skew Index'''
        self.from_date = from_date   
        self.params = ['upper', 'lower', 'above_up', 'below_low']

        #Data and model parameters
        self.avg_window = 30
        self.benchmark = benchmark
        self.data = data
        self.upper = 0.5
        self.lower = -0.5


        self.above_up = -1
        self.below_low = 1
        self.other = 0
        
        ModelAdmin.__init__(self)
    
    def indicator(self):

        data = self.data.copy()[[self.benchmark,'SKEW.INDX']]
        data.columns = [self.benchmark, self.code]
        data['ZSCORE'] = data[self.code].rolling(window=self.avg_window).apply(lambda x: (x.iloc[-1] - x.mean()) / x.std())

        data.loc[data['ZSCORE']>self.upper, 'SIGNAL'] = self.above_up
        data.loc[data['ZSCORE']<self.lower, 'SIGNAL'] = self.below_low
        data['SIGNAL'] = data['SIGNAL'].fillna(self.other)
        data = data.dropna()
        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:['SKEW'], 
                     2:['ZSCORE']}

        self.last_stats = data.iloc[-1]
        self.last_update = data.index[-1]
        return data
    

class TermSt(ModelAdmin):
    def __init__(self, data, benchmark='SPY', from_date='2022-05-16 00:00'):
        #Meta information
        self.name = 'TERM'
        self.code = 'TERM'
        self.description = '''Term Structure Slope'''
        self.from_date = from_date   
        self.params = ['upper', 'lower', 'above_up', 'below_low']

        #Data and model parameters
        self.benchmark = benchmark
        self.data = data
        self.upper = 0.5
        self.lower = -0.5


        self.above_up = -1
        self.below_low = 1
        self.other = 0
        
        ModelAdmin.__init__(self)
    
    def indicator(self):

        data = self.data.copy()[[self.benchmark,'VIX9D.INDX', 'VIX3M.INDX']]
        data.columns = [self.benchmark, 'VIX9D', 'VIX3M']
        data['RATIO'] = data['VIX9D']/data['VIX3M'] - 1

        data.loc[data['RATIO']>self.upper, 'SIGNAL'] = self.above_up
        data.loc[data['RATIO']<self.lower, 'SIGNAL'] = self.below_low
        data['SIGNAL'] = data['SIGNAL'].fillna(self.other)
        data = data.dropna()
        self.model_data = data
        self.signal = data[['SIGNAL']]
        self.signal.columns = [self.code]

        self.axis = {0:[self.benchmark],
                     1:['VIX9D', 'VIX3M'], 
                     2:['RATIO']}

        self.last_stats = data.iloc[-1]
        self.last_update = data.index[-1]
        return data