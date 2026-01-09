from dash import Dash, html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import models
import pickle
import os
import json


# Get the directory where app.py actually lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
#obj = models.Composite([
#                        models.VolSpread,
#                        models.VolAutocorr,
#                        models.VixSpread, 
#                        models.GEX
#                    ])

data_obj = models.Data()

MODEL_LIST  = [models.VolSpread, 
               models.VolAutocorr, 
               models.VixSpread, 
               models.GEX]

def saved_models():
    models = [{'label':x, 'value':x} for x in os.listdir(MODELS_DIR)]
    return models

colors={
        1:'success', 
        -1:'danger', 
        0:'warning', 
        }
signals={
        1:'Green', 
        -1:'Red', 
        0:'Yellow', 
        }

def composite_inputs(obj):
    code='COMPOSITE'
    conta = dbc.Container([
        dbc.Row([
            dbc.Col(html.P('Traffic Light')), 
            dbc.Col(dbc.Badge(signals[obj.last_stats['SIGNAL']], color=colors[obj.last_stats['SIGNAL']], className="me-1", id=f"{code}-signal-badge"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Vol-VIX Spread')), 
            dbc.Col(dbc.Badge(signals[obj.models['VOLSPREAD'].last_stats['SIGNAL']], color=colors[obj.models['VOLSPREAD'].last_stats['SIGNAL']], className="me-1", id=f"VOLSPREAD-signal-badge"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Autocorrelation')), 
            dbc.Col(dbc.Badge(signals[obj.models['VOLAUTOCORR'].last_stats['SIGNAL']], color=colors[obj.models['VOLAUTOCORR'].last_stats['SIGNAL']], className="me-1", id=f"VOLAUTOCORR-signal-badge"))
                ]),
        dbc.Row([
            dbc.Col(html.P('VIX-VVIX Spread')), 
            dbc.Col(dbc.Badge(signals[obj.models['VIXVVIX'].last_stats['SIGNAL']], color=colors[obj.models['VIXVVIX'].last_stats['SIGNAL']], className="me-1", id=f"VIXVVIX-signal-badge"))
                ]),
        dbc.Row([
            dbc.Col(html.P('GEX')), 
            dbc.Col(dbc.Badge(signals[obj.models['GEX'].last_stats['SIGNAL']], color=colors[obj.models['GEX'].last_stats['SIGNAL']], className="me-1", id=f"GEX-signal-badge"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Last Update')), 
            dbc.Col(html.P(f"{obj.last_update.strftime('%Y-%m-%d')}", id=f"{code}-date"))
                ]),
        dbc.Row([
            dbc.Col(html.H6('Inputs')),
                ]),
        dbc.Row([
            dbc.Col(html.P('Upper Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-upper-band', value=obj.upper, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Lower Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-lower-band', value=obj.lower, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Above Upper')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-above-upper', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.above_up))
                ]),
        dbc.Row([
            dbc.Col(html.P('Below Lower')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-below-lower', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.below_low))
                ]),
        dbc.Row([
            dbc.Col(
                dbc.Button("Submit", id=f"{code}-submit-btn", color="primary", className="mt-2")
            ), 
                ])
    ])
    return conta

def volspread_inputs(obj):
    code='VOLSPREAD'
    conta = dbc.Container([
        dbc.Row([
            dbc.Col(html.P('Actual Volatility')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['ACTVOL']/100:.2%}", id=f"{code}-act-vol"))
                ]),
        dbc.Row([
            dbc.Col(html.P('VIX 1Day Index')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['VIX1D.INDX']/100:.2%}", id=f"{code}-vix-indx"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Ratio')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['VOLRATIO']:.2f}", id=f"{code}-ratio"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Moving Average')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['AVGRATIO']:.2f}", id=f"{code}-avg-ratio"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Signal')), 
            dbc.Col(dbc.Badge(signals[obj.models[code].last_stats['SIGNAL']], color=colors[obj.models[code].last_stats['SIGNAL']], className="me-1", id=f"{code}-signal-badge"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Last Update')), 
            dbc.Col(html.P(f"{obj.models[code].last_update.strftime('%Y-%m-%d')}", id=f"{code}-date"))
                ]),
        dbc.Row([
            dbc.Col(html.H6('Inputs')), 
                ]),
        dbc.Row([
            dbc.Col(html.P('Average Window')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-avg-window', value=obj.models[code].avg_window, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Upper Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-upper-band', value=obj.models[code].upper, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Lower Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-lower-band', value=obj.models[code].lower, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Above Upper')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-above-upper', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.models[code].above_up))
                ]),
        dbc.Row([
            dbc.Col(html.P('Below Lower')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-below-lower', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.models[code].below_low))
                ]),
        dbc.Row([
            dbc.Col(
                dbc.Button("Submit", id=f"{code}-submit-btn", color="primary", className="mt-2")
            ), 
                ])
    ])
    return conta

def volautocorr_inputs(obj):
    code='VOLAUTOCORR'
    conta = dbc.Container([
        dbc.Row([
            dbc.Col(html.P('Volatiliy Autocorrelation')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['AUTOCORR']:.2f}", id=f"{code}-autocorr"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Signal')), 
            dbc.Col(dbc.Badge(signals[obj.models[code].last_stats['SIGNAL']], color=colors[obj.models[code].last_stats['SIGNAL']], className="me-1", id=f"{code}-signal-badge"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Last Update')), 
            dbc.Col(html.P(f"{obj.models[code].last_update.strftime('%Y-%m-%d')}", id=f"{code}-date"))
                ]),
        dbc.Row([
            dbc.Col(html.H6('Inputs')), 
                ]),
        dbc.Row([
            dbc.Col(html.P('Autocorr Lag')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-lag', value=obj.models[code].lag, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Upper Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-upper-band', value=obj.models[code].upper, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Lower Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-lower-band', value=obj.models[code].lower, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Above Upper')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-above-upper', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.models[code].above_up))
                ]),
        dbc.Row([
            dbc.Col(html.P('Below Lower')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-below-lower', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.models[code].below_low))
                ]),
        dbc.Row([
            dbc.Col(
                dbc.Button("Submit", id=f"{code}-submit-btn", color="primary", className="mt-2")
            ), 
                ])
    ])
    return conta

def vixvvix_inputs(obj):
    code='VIXVVIX'
    conta = dbc.Container([
        dbc.Row([
            dbc.Col(html.P('VIX Index')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['VIX.INDX']/100:.2%}", id=f"{code}-vix"))
                ]),
        dbc.Row([
            dbc.Col(html.P('VVIX Index')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['VVIX.INDX']/100:.2%}", id=f"{code}-vvix"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Difference')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['VIXDIF']:.2f}", id=f"{code}-diff"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Moving Average')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['AVGDIF']:.2f}", id=f"{code}-avg-diff"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Signal')), 
            dbc.Col(dbc.Badge(signals[obj.models[code].last_stats['SIGNAL']], color=colors[obj.models[code].last_stats['SIGNAL']], className="me-1", id=f"{code}-signal-badge"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Last Update')), 
            dbc.Col(html.P(f"{obj.models[code].last_update.strftime('%Y-%m-%d')}", id=f"{code}-date"))
                ]),
        dbc.Row([
            dbc.Col(html.H6('Inputs')), 
                ]),
        dbc.Row([
            dbc.Col(html.P('Average Window')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-avg-window', value=obj.models[code].avg_window, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Upper Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-upper-band', value=obj.models[code].upper, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Lower Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-lower-band', value=obj.models[code].lower, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Above Upper')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-above-upper', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.models[code].above_up))
                ]),
        dbc.Row([
            dbc.Col(html.P('Below Lower')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-below-lower', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.models[code].below_low))
                ]),
        dbc.Row([
            dbc.Col(
                dbc.Button("Submit", id=f"{code}-submit-btn", color="primary", className="mt-2")
            ), 
                ])
    ])
    return conta


def gex_inputs(obj):
    code='GEX'
    conta = dbc.Container([
        dbc.Row([
            dbc.Col(html.P('Gamma Exposure')), 
            dbc.Col(html.P(f"{obj.models[code].last_stats['GEX']}", id=f"{code}-gex"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Signal')), 
            dbc.Col(dbc.Badge(signals[obj.models[code].last_stats['SIGNAL']], color=colors[obj.models[code].last_stats['SIGNAL']], className="me-1", id=f"{code}-signal-badge"))
                ]),
        dbc.Row([
            dbc.Col(html.P('Last Update')), 
            dbc.Col(html.P(f"{obj.models[code].last_update.strftime('%Y-%m-%d')}", id=f"{code}-date"))
                ]),
        dbc.Row([
            dbc.Col(html.H6('Inputs')), 
                ]),
        dbc.Row([
            dbc.Col(html.P('Upper Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-upper-band', value=obj.models[code].upper, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Lower Band')), 
            dbc.Col(dbc.Input(size='sm',id=f'{code}-lower-band', value=obj.models[code].lower, type='number'))
                ]),
        dbc.Row([
            dbc.Col(html.P('Above Upper')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-above-upper', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.models[code].above_up))
                ]),
        dbc.Row([
            dbc.Col(html.P('Below Lower')), 
            dbc.Col(dbc.Select(size='sm',id=f'{code}-below-lower', 
                               options= [
                                   {'label':'Red', 'value':-1}, 
                                   {'label':'Yellow', 'value':0}, 
                                   {'label':'Green', 'value':1}
                                   ],
                               value=obj.models[code].below_low))
                ]),
        dbc.Row([
            dbc.Col(
                dbc.Button("Submit", id=f"{code}-submit-btn", color="primary", className="mt-2")
            ), 
                ])
    ])
    return conta


def main_display(inputs=None):
    row = dbc.Row([
            dbc.Col([inputs]),
            dbc.Col([
                dcc.Loading(
                    id="loading-1", 
                    type="default",
                    children=dcc.Graph(id='indicator-chart')
                )
            ], className='col-9'), 
        ], className='bg-light pt-1')
    return row

app.layout = html.Div([
    dcc.Store(id='session-store', storage_type='session'),
    # 1. The Navbar sits here, independent of the content container
    dbc.Navbar(
        dbc.Container(
            dbc.NavbarBrand("VolEcology Dashboard", className="fs-2"),
            fluid=True, # Aligns text with the container content below
        ),
        color="light",
        dark=False,
        className="border-bottom shadow-sm mb-4" # Professional styling
    ),
    
    # 2. The main content container
    dbc.Container([
        dcc.Loading(
            id="loading-initialization",
            type="default",
            fullscreen=True,
            children=html.Div(id="main-content")
        )
    ], fluid=True) # fluid=True allows the graphs below to be wide
], style={'margin': '0px', 'padding': '0px'}) # Removes tiny browser gaps at the edges

@app.callback(Output("main-content", "children"),
              Output('session-store', 'data'), 
              Input("loading-initialization", "id"))
def initialize_app(_):
    data_obj.load_data()

    path = os.path.join(MODELS_DIR, 'default.json') # os.listdir already includes .json


    # 1. Load the JSON
    with open(path, 'r') as f:
        data_dict = json.load(f)

    obj = models.Composite(MODEL_LIST, data_obj.data)
    obj.load_models()
    obj.from_dict(data_dict) 
    obj.indicator()

    layout_content = [
        dbc.Row([
            dbc.Col([dbc.Select(size='sm', id='select-model', options=saved_models()),
                     html.P('Loaded default', id='loaded-status')], className='col-2'),
            dbc.Col(dbc.Button('Load', id='load-model', color='primary'), className='col-2'),
            dbc.Col([dbc.Input(size='sm', id='save-as', type='text'),
                     html.P('Not saved', id='saved-status')], className='col-2 mt-2'),
            dbc.Col(dbc.Button('Save As', id='save-model', color='primary'), className='col-2 mt-2'),
                ]),            
        dbc.Tabs([
            dbc.Tab(label="Composite", tab_id="COMPOSITE"),
            dbc.Tab(label="Vol-VIX Spread", tab_id="VOLSPREAD"),
            dbc.Tab(label="Autocorrelation", tab_id="VOLAUTOCORR"),
            dbc.Tab(label="VIX-VVIX Spread", tab_id="VIXVVIX"), 
            dbc.Tab(label="GEX", tab_id="GEX")
        ], id="tabs", active_tab="COMPOSITE", className="mb-3 mt-3"),
        html.Div(id="tabs-content")
    ]
    return layout_content, obj.to_dict()

@app.callback(Output("tabs-content", "children"), 
              Input("tabs", "active_tab"), 
              State('session-store', 'data'))
def render_content(active_tab, session_store):
    print(session_store)
    obj = models.Composite(MODEL_LIST, data_obj.data)
    obj.load_models()
    obj.from_dict(session_store)
    obj.indicator()

    if active_tab == "VOLSPREAD":
        return main_display(inputs=volspread_inputs(obj))
    elif active_tab == "VOLAUTOCORR":
        return main_display(inputs=volautocorr_inputs(obj))
    elif active_tab == "VIXVVIX":
        return main_display(inputs=vixvvix_inputs(obj))
    elif active_tab== "GEX":
        return main_display(inputs=gex_inputs(obj))
    elif active_tab == "COMPOSITE":
        return main_display(inputs=composite_inputs(obj))
         
    return html.P("No tab selected")

@app.callback(
    Output('indicator-chart', 'figure'),
    Input('tabs', 'active_tab'),
    State('session-store', 'data'))

def update_chart(active_tab, session_store):
    obj = models.Composite(MODEL_LIST, data_obj.data)
    obj.load_models()
    obj.from_dict(session_store)
    obj.indicator()

    if active_tab == "COMPOSITE":
        fig = obj.plot_indicator_plotly()
        return fig
    else:
        fig = obj.models[active_tab].plot_indicator_plotly()
        return fig

@app.callback(
    Output(f'indicator-chart', 'figure', allow_duplicate=True),
    Output(f'VOLSPREAD-act-vol', 'children'),
    Output(f'VOLSPREAD-vix-indx', 'children'),
    Output(f'VOLSPREAD-ratio', 'children'),
    Output(f'VOLSPREAD-avg-ratio', 'children'),
    Output(f'VOLSPREAD-signal-badge', 'children'),
    Output(f'VOLSPREAD-signal-badge', 'color'),
    Output(f'session-store', 'data', allow_duplicate=True), 
    Input(f'VOLSPREAD-submit-btn', 'n_clicks'),
    State(f'VOLSPREAD-avg-window', 'value'),
    State(f'VOLSPREAD-upper-band', 'value'),
    State(f'VOLSPREAD-lower-band', 'value'),
    State(f'VOLSPREAD-above-upper', 'value'),
    State(f'VOLSPREAD-below-lower', 'value'),
    State(f'session-store', 'data'),
    prevent_initial_call=True
)
def update_volspread(n_clicks, avg_window, upper, lower, above_up, below_low, session_store):

    obj = models.Composite(MODEL_LIST, data_obj.data)
    obj.load_models()
    obj.from_dict(session_store)
    obj.indicator()

    obj.models['VOLSPREAD'].avg_window = avg_window
    obj.models['VOLSPREAD'].upper = upper
    obj.models['VOLSPREAD'].lower = lower
    obj.models['VOLSPREAD'].above_up = int(above_up)
    obj.models['VOLSPREAD'].below_low = int(below_low)
    
    obj.refresh_models()
    obj.indicator()

    session_store = obj.to_dict()


    fig = obj.models['VOLSPREAD'].plot_indicator_plotly()
    
    stats = obj.models['VOLSPREAD'].last_stats
    act_vol = f"{stats['ACTVOL']/100:.2%}"
    vix_indx = f"{stats['VIX1D.INDX']/100:.2%}"
    ratio = f"{stats['VOLRATIO']:.2f}"
    avg_ratio = f"{stats['AVGRATIO']:.2f}"
    signal_label = signals[stats['SIGNAL']]
    signal_color = colors[stats['SIGNAL']]

    return fig, act_vol, vix_indx, ratio, avg_ratio, signal_label, signal_color, session_store
    
@app.callback(
    Output(f'indicator-chart', 'figure', allow_duplicate=True),
    Output(f'VOLAUTOCORR-autocorr', 'children'),
    Output(f'VOLAUTOCORR-signal-badge', 'children'),
    Output(f'VOLAUTOCORR-signal-badge', 'color'),
    Output(f'session-store', 'data', allow_duplicate=True), 
    Input(f'VOLAUTOCORR-submit-btn', 'n_clicks'),
    State(f'VOLAUTOCORR-lag', 'value'),
    State(f'VOLAUTOCORR-upper-band', 'value'),
    State(f'VOLAUTOCORR-lower-band', 'value'),
    State(f'VOLAUTOCORR-above-upper', 'value'),
    State(f'VOLAUTOCORR-below-lower', 'value'),
    State(f'session-store', 'data'),
    prevent_initial_call=True
)
def update_volautocorr(n_clicks, lag, upper, lower, above_up, below_low, session_store):
    obj = models.Composite(MODEL_LIST, data_obj.data)
    obj.load_models()
    obj.from_dict(session_store)
    obj.indicator()

    obj.models['VOLAUTOCORR'].lag = lag
    obj.models['VOLAUTOCORR'].upper = upper
    obj.models['VOLAUTOCORR'].lower = lower
    obj.models['VOLAUTOCORR'].above_up = int(above_up)
    obj.models['VOLAUTOCORR'].below_low = int(below_low)

    obj.refresh_models()
    obj.indicator()

    session_store = obj.to_dict()

    fig = obj.models['VOLAUTOCORR'].plot_indicator_plotly()
    
    stats = obj.models['VOLAUTOCORR'].last_stats

    autocorr = f"{stats['AUTOCORR']:.2f}"
    signal_label = signals[stats['SIGNAL']]
    signal_color = colors[stats['SIGNAL']]

    return fig, autocorr, signal_label, signal_color, session_store


@app.callback(
    Output(f'indicator-chart', 'figure', allow_duplicate=True),
    Output(f'VIXVVIX-vix', 'children'),
    Output(f'VIXVVIX-vvix', 'children'),
    Output(f'VIXVVIX-diff', 'children'),
    Output(f'VIXVVIX-avg-diff', 'children'),
    Output(f'VIXVVIX-signal-badge', 'children'),
    Output(f'VIXVVIX-signal-badge', 'color'),
    Output(f'session-store', 'data', allow_duplicate=True), 
    Input(f'VIXVVIX-submit-btn', 'n_clicks'),
    State(f'VIXVVIX-avg-window', 'value'),
    State(f'VIXVVIX-upper-band', 'value'),
    State(f'VIXVVIX-lower-band', 'value'),
    State(f'VIXVVIX-above-upper', 'value'),
    State(f'VIXVVIX-below-lower', 'value'),
    State(f'session-store', 'data'),
    prevent_initial_call=True
)
def update_VIXVVIX(n_clicks, avg_window, upper, lower, above_up, below_low, session_store):

    obj = models.Composite(MODEL_LIST, data_obj.data)
    obj.load_models()
    obj.from_dict(session_store)
    obj.indicator()

    obj.models['VIXVVIX'].avg_window = avg_window
    obj.models['VIXVVIX'].upper = upper
    obj.models['VIXVVIX'].lower = lower
    obj.models['VIXVVIX'].above_up = int(above_up)
    obj.models['VIXVVIX'].below_low = int(below_low)
    
    obj.refresh_models()
    obj.indicator()

    session_store = obj.to_dict()

    fig = obj.models['VIXVVIX'].plot_indicator_plotly()
    
    stats = obj.models['VIXVVIX'].last_stats
    vix = f"{stats['VIX.INDX']/100:.2%}"
    vvix = f"{stats['VVIX.INDX']/100:.2%}"
    dif = f"{stats['VIXDIF']:.2f}"
    avg_dif = f"{stats['AVGDIF']:.2f}"
    signal_label = signals[stats['SIGNAL']]
    signal_color = colors[stats['SIGNAL']]

    return fig, vix, vvix, dif, avg_dif, signal_label, signal_color, session_store

@app.callback(
    Output(f'indicator-chart', 'figure', allow_duplicate=True),
    Output(f'GEX-gex', 'children'),
    Output(f'GEX-signal-badge', 'children'),
    Output(f'GEX-signal-badge', 'color'),
    Output(f'session-store', 'data', allow_duplicate=True), 
    Input(f'GEX-submit-btn', 'n_clicks'),
    State(f'GEX-upper-band', 'value'),
    State(f'GEX-lower-band', 'value'),
    State(f'GEX-above-upper', 'value'),
    State(f'GEX-below-lower', 'value'),
    State(f'session-store', 'data'),
    prevent_initial_call=True
)
def update_GEX(n_clicks,  upper, lower, above_up, below_low, session_store):

    obj = models.Composite(MODEL_LIST, data_obj.data)
    obj.load_models()
    obj.from_dict(session_store)
    obj.indicator()

    obj.models['GEX'].upper = upper
    obj.models['GEX'].lower = lower
    obj.models['GEX'].above_up = int(above_up)
    obj.models['GEX'].below_low = int(below_low)
    
    obj.refresh_models()
    obj.indicator()

    session_store = obj.to_dict()

    fig = obj.models['GEX'].plot_indicator_plotly()
    
    stats = obj.models['GEX'].last_stats
    gex = stats['GEX']

    signal_label = signals[stats['SIGNAL']]
    signal_color = colors[stats['SIGNAL']]

    return fig, gex, signal_label, signal_color, session_store





@app.callback(
    Output(f'indicator-chart', 'figure', allow_duplicate=True),
    Output(f'COMPOSITE-signal-badge', 'children'),
    Output(f'COMPOSITE-signal-badge', 'color'),  
    Output(f'session-store', 'data', allow_duplicate=True), 
    Input(f'COMPOSITE-submit-btn', 'n_clicks'),
    State(f'COMPOSITE-upper-band', 'value'),
    State(f'COMPOSITE-lower-band', 'value'),
    State(f'COMPOSITE-above-upper', 'value'),
    State(f'COMPOSITE-below-lower', 'value'),
    State(f'session-store', 'data'),
    prevent_initial_call=True
)
def update_COMPOSITE(n_clicks,  upper, lower, above_up, below_low, session_store):

    obj = models.Composite(MODEL_LIST, data_obj.data)
    obj.load_models()
    obj.from_dict(session_store)
    obj.indicator()

    obj.upper = upper
    obj.lower = lower
    obj.above_up = int(above_up)
    obj.below_low = int(below_low)

    obj.refresh_models()
    obj.indicator()

    session_store = obj.to_dict()

    fig = obj.plot_indicator_plotly()
    
    stats = obj.last_stats
    signal_label = signals[stats['SIGNAL']]
    signal_color = colors[stats['SIGNAL']]

    return fig, signal_label, signal_color, session_store

@app.callback(
    Output(f'saved-status', 'children'),
    Input(f'save-model', 'n_clicks'),
    State(f'save-as', 'value'),
    State(f'session-store', 'data'),
    prevent_initial_call=True)
def save_model(n_clicks, save_as, session_store):
    # 1. Guard against initial load
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate

    if not save_as:
        return "Please provide a filename"

    try:
        # 2. Setup Object (Skip .indicator() if it's just for math)
        obj = models.Composite(MODEL_LIST, data_obj.data)
        obj.load_models()
        obj.from_dict(session_store)
        
        # 3. Construct Path correctly
        path = os.path.join(MODELS_DIR, f"{save_as}.json")
        
        # 4. Save using 'w' (Text mode)
        with open(path, 'w') as f:
            json.dump(obj.to_dict(), f, indent=4)
            
        return f'Successfully saved as {save_as}'

    except Exception as e:
        # Log the actual error to your terminal so you can debug
        print(f"Save Error: {e}") 
        return f"Error saving file: {str(e)}"

@app.callback(
    Output('loaded-status', 'children'),
    Output('tabs-content', 'children', allow_duplicate=True), 
    Output('indicator-chart', 'figure', allow_duplicate=True),
    Output('session-store', 'data', allow_duplicate=True), # CRITICAL: Update the store
    Input('load-model', 'n_clicks'),
    State('select-model', 'value'),
    State('tabs', 'active_tab'),
    prevent_initial_call=True
)
def load_model(n_clicks, select_model, active_tab):
    if not n_clicks or not select_model:
        raise PreventUpdate

    path = os.path.join(MODELS_DIR, select_model) # os.listdir already includes .json

    try:
        # 1. Load the JSON
        with open(path, 'r') as f:
            data_dict = json.load(f)
        
        # 2. Reconstruct and Calculate
        new_obj = models.Composite(MODEL_LIST, data_obj.data)
        new_obj.load_models() # Ensure sub-models are initialized
        new_obj.from_dict(data_dict) 
        new_obj.indicator() 

        # 3. Prepare the specific UI for the current tab
        if active_tab == "VOLSPREAD":
            new_ui = volspread_inputs(new_obj)
            fig = new_obj.models['VOLSPREAD'].plot_indicator_plotly()
        elif active_tab == "VOLAUTOCORR":
            new_ui = volautocorr_inputs(new_obj)
            fig = new_obj.models['VOLAUTOCORR'].plot_indicator_plotly()
        elif active_tab == "VIXVVIX":
            new_ui = vixvvix_inputs(new_obj)
            fig = new_obj.models['VIXVVIX'].plot_indicator_plotly()
        elif active_tab == "GEX":
            new_ui = gex_inputs(new_obj)
            fig = new_obj.models['GEX'].plot_indicator_plotly()
        else: # COMPOSITE
            new_ui = composite_inputs(new_obj)
            fig = new_obj.plot_indicator_plotly()

        # 4. Return everything: Status, UI, Chart, and updated Store
        return (
            f'Successfully loaded {select_model}', 
            main_display(inputs=new_ui), 
            fig, 
            new_obj.to_dict() 
        )
        
    except Exception as e:
        import traceback
        print(traceback.format_exc()) # Prints the full error to your terminal
        return f"Error: {str(e)}"



if __name__ == '__main__':
    app.run(debug=True)
