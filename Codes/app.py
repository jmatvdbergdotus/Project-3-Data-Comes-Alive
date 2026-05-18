import dash
from dash import dcc, html, dash_table, State
from dash.dependencies import Input, Output
import pandas as pd
import sqlite3
import plotly.express as px
import numpy as np
from datetime import datetime


# Database Path (Ensure this matches your folder structure)
data_file = "Data/baggage_handling.db"

def get_data():
    conn = sqlite3.connect(data_file)
    query = """
    SELECT e.*, b.terminal, b.zone, b.priority 
    FROM Event e 
    JOIN Bag b ON e.BagID = b.BagID
    """
    df = pd.read_sql(query, conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    # Convert result to string for better legend labeling
    df['status'] = df['result'].map({1: 'Success', 0: 'Failure/Jam'})

    if 'temperature' not in df.columns:
        np.random.seed(42)
        df['temperature'] = np.where(df['result'] == 1, 
                                     np.random.normal(27, 4, size=len(df)), 
                                     np.random.normal(43, 5, size=len(df)))
    if 'vibration' not in df.columns:
        np.random.seed(99)
        df['vibration'] = np.where(df['result'] == 1, 
                                   np.random.normal(2.5, 0.6, size=len(df)), 
                                   np.random.normal(6.8, 1.2, size=len(df)))
        
    conn.close()
    return df

df = get_data()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

CARD_STYLE = {
    'backgroundColor': '#1e293b',
    'padding': '20px',
    'borderRadius': '20px',
    'boxShadow': '0 4px 15px rgba(0,0,0,0.3)',
    'marginBottom': '20px'
}

# --- PAGE 1: SYSTEM OVERVIEW ---
def page_1_layout():
    return html.Div([
        html.H2(
            "System Overview in the last 24 Hours",

            style={
                'color': '#7FFF00',

                'position': 'sticky',
                'top': '110px',
                'zIndex': '998',
                'backgroundColor': 'rgba(15, 23, 42, 0.9)',
                'backdropFilter': 'blur(8px)',
                'padding': '15px',
                'borderRadius': '10px',
                'boxShadow': '0 2px 10px rgba(0,0,0,0.3)'
            }
        ),
        html.Div([
            html.Label("Select Terminal:"),
            dcc.Dropdown(
                id='terminal-dropdown',
                options=[{'label': i, 'value': i} for i in df['terminal'].unique()],
                value=df['terminal'].unique().tolist(),
                multi=True,
                style={'color': '#000000'}
            ),
        ], style={'padding': '20px'}),

        html.Div([

            html.Div([
                html.H4("Total Bags"),
                html.H2(f"{df['BagID'].nunique()}"),
            ], style={
                **CARD_STYLE,
                'width': '20%',
                'display': 'inline-block',
                'textAlign': 'center',
                'marginRight': '15px'
            }),

            html.Div([
                html.H4("Failure Events"),
                html.H2(f"{(df['result']==0).sum()}"),
            ], style={
                **CARD_STYLE,
                'width': '20%',
                'display': 'inline-block',
                'textAlign': 'center',
                'marginRight': '15px'
            }),

            html.Div([
                html.H4("Success Rate"),
                html.H2(
                    f"{round((df['result']==1).mean()*100,2)}%"
                ),
            ], style={
                **CARD_STYLE,
                'width': '20%',
                'display': 'inline-block',
                'textAlign': 'center',
                'marginRight': '15px'
            }),

            html.Div([
                html.H4("Average Delay"),
                html.H2(
                    f"{round(df['delay'].mean(),2)} min"
                ),
            ], style={
                **CARD_STYLE,
                'width': '20%',
                'display': 'inline-block',
                'textAlign': 'center'
            })

        ], style={
            'marginBottom': '30px'
        }),

        html.Div([
            html.Div([
                dcc.Graph(id='throughput-graph')
        ], style={
            **CARD_STYLE,
            'width': '45%',
            'display': 'inline-block'
        }),

            html.Div([
                dcc.Graph(id='location-risk-heatmap')
            ], style={
            **CARD_STYLE,
            'width': '45%', 
            'float': 'right', 
            'display': 'inline-block'
        })
        ]),
    ])

def page_2_layout():
    return html.Div([
        html.H2("Process Performance & Delays in the last 24 Hours", 
                style={
                'color': '#7FFF00',

                'position': 'sticky',
                'top': '110px',
                'zIndex': '998',
                'backgroundColor': 'rgba(15, 23, 42, 0.9)',
                'backdropFilter': 'blur(8px)',
                'padding': '15px',
                'borderRadius': '10px',
                'boxShadow': '0 2px 10px rgba(0,0,0,0.3)'
            }
        ),
        
        html.Div([
            # Graph 1: Delay Distribution
            html.Div([
                dcc.Graph(id='delay-dist-boxplot')
            ], style={
                **CARD_STYLE,
                'width': '45%', 'display': 'inline-block'}),
            
            # Graph 2: Success vs Failure Rate
            html.Div([
                dcc.Graph(id='success-failure-bar')
            ], style={
                **CARD_STYLE,
                'width': '45%', 'float': 'right', 'display': 'inline-block'})
        ]),
        
        html.Div([
            html.Div([
                dcc.Graph(id='priority-performance-bar')
            ], style={
                **CARD_STYLE, 'width': '45%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id='sensor-correlation-scatter')
            ], style={
                **CARD_STYLE, 'width': '45%', 'float': 'right', 'display': 'inline-block'})
        ]),


# --- MAIN LAYOUT ---
app.layout = html.Div(
    
    style={
        'background': 'linear-gradient(135deg, #0f172a, #1e293b)',
        'minHeight': '100vh',
        'color': 'white',
        'padding': '30px',
        'fontFamily': 'Segoe UI'
    }, 
    
    children=[
        dcc.Store(id='page-index', data=0),

        dcc.Interval(
            id='interval-component',
            interval=1000,
            n_intervals=0
        ),
        html.Div([
            html.H1(
                "Airport Baggage Control Dashboard",
                style={
                    'textAlign': 'center',
                    'color': "#87CEFA",
                    'marginTop': '0px',
                    'marginBottom': '5px'
                }
            ),

            html.Div([

                html.H3(
                    "● LIVE SYSTEM",
                    style={
                        'color': '#22c55e',
                        'margin': '0'
                    }
                ),

                html.P(
                    id='live-time',
                    style={'margin': '0'}
                )

            ], style={
                'textAlign': 'center'
            })

        ], style={

            'position': 'sticky',
            'top': '0',
            'zIndex': '999',

            'backgroundColor': '#0f172a',

            'padding': '15px',

            'borderBottom': '2px solid #38bdf8',

            'boxShadow': '0 4px 10px rgba(0,0,0,0.4)'
        }),

        html.Div(
            id='page-content',
            style={'marginTop': '20px'}
        ),

        html.Div([
            html.Button(
                "← Back",
             id="back-btn",
                n_clicks=0,
                style={'marginRight': '10px'}
            ),

            html.Button(
                "Next →",
                id="next-btn",
                n_clicks=0,
                style={'backgroundColor': '#00d4ff'}
            )

        ], style={
            'textAlign': 'center',
            'marginTop': '30px'
        })
    ]
)
# --- CALLBACK: NAVIGATION ---
@app.callback(
    [Output('page-content', 'children'),
     Output('page-index', 'data'),
     Output('next-btn', 'style'),
     Output('back-btn', 'style')],
    [Input('next-btn', 'n_clicks'),
     Input('back-btn', 'n_clicks')],
    [State('page-index', 'data')]
)
def navigate(n_next, n_back, current_index):
    ctx = dash.callback_context
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'next-btn':
            current_index = min(current_index + 1, 1)
        elif button_id == 'back-btn':
            current_index = max(current_index - 1, 0)
    
    # Define styles based on current page index
    next_style = {'backgroundColor': '#00d4ff', 'display': 'inline-block'}
    back_style = {'marginRight': '10px', 'display': 'inline-block'}
    
    if current_index == 1:
        next_style['display'] = 'none'  # Remove Next button on Page 2
        return page_2_layout(), current_index, next_style, back_style
    else:
        back_style['display'] = 'none'  # Remove Back button on Page 1
        return page_1_layout(), current_index, next_style, back_style

# --- CALLBACK: PAGE 1 GRAPHS ---
@app.callback(
    [Output('throughput-graph', 'figure'),
     Output('location-risk-heatmap', 'figure')],
    [Input('terminal-dropdown', 'value')]
)
def update_page_1(selected_terminals):
    if not selected_terminals: return px.scatter(), px.scatter()
    filtered = df[df['terminal'].isin(selected_terminals)]
    
    fig1 = px.area(
        filtered.groupby('hour')['BagID'].nunique().reset_index(),
        x='hour',
        y='BagID',
        title="Bags Per Hour",
        template="plotly_dark"
    )

    fig1.update_layout(
        yaxis_title="BagCount",
        paper_bgcolor='#1e293b',
        plot_bgcolor='#1e293b',
        font_color='white',
        title_font_size=22,
        title_x=0.5
    )
    
    fig2 = px.density_heatmap(
        filtered.groupby(['terminal', 'zone'])['result'].apply(lambda x: (x==0).sum()).reset_index(),
        x='zone', 
        y='terminal', 
        z='result', 
        title="Technical Errors Heatmap", 
        template="plotly_dark")
    
    fig2.update_layout(
        paper_bgcolor='#1e293b',
        plot_bgcolor='#1e293b',
        font_color='white',
        title_font_size=22,
        title_x=0.5
    )

    return fig1, fig2

# --- CALLBACK: PAGE 2 GRAPHS (PROCESS DELAYS & SUCCESS RATES) ---
@app.callback(
    [Output('delay-dist-boxplot', 'figure'),
     Output('success-failure-bar', 'figure'),
     Output('priority-performance-bar', 'figure')],
     Output('sensor-correlation-scatter', 'figure')],
    [Input('page-index', 'data')] # Updates when you switch to Page 2
)
def update_page_2(index):
    if index != 1: return dash.no_update, dash.no_update, dash.no_update
    
    # 1. Process Delay Boxplot (Excluding 0 delays from initial steps)
    fig_box = px.box(df[df['delay'] > 0], x='process', y='delay', color='process',
                     title="Process Delay Distribution (Minutes)",
                     template="plotly_dark", points="all")
    
    # 2. Success/Failure Bar Chart
    # Group by process and status to get counts
    sf_counts = df.groupby(['process', 'status']).size().reset_index(name='counts')
    fig_bar = px.bar(
        sf_counts, 
        x='process', 
        y='counts', 
        color='status',
        barmode='group', 
        title="Success vs. Failure Count per Process",
        color_discrete_map={'Success': '#2ecc71', 'Failure/Jam': '#e74c3c'},
        template="plotly_dark"
    )
    
    process_priority_avg = df.groupby(['process', 'Priority'])['delay'].mean().reset_index()
    process_priority_avg['Priority'] = process_priority_avg['Priority'].map({
    1: 'Priority Bags',
    0: 'Normal Bags'
    })
    fig_priority_process = px.bar(
        process_priority_avg, 
        x='process', 
        y='delay', 
        color='Priority',  # Using the exact casing
        barmode='group',   # Puts bars side-by-side
        title="Average Delay by Process & Priority",

        color_discrete_map={
        'Priority Bags': '#F08080',
        'Normal Bags': '#00FFFF'
        },

        template="plotly_dark"
    )
    fig_priority_process.update_layout(
    paper_bgcolor='#1e293b',
    plot_bgcolor='#1e293b',
    font_color='white',
    title_x=0.5
    )
    fig_priority_process.update_traces(
    marker_line_width=0
    )
    fig_sensor = px.scatter(
        df,
        x='temperature',
        y='vibration',
        color='status',
        color_discrete_map={'Success': '#2ecc71', 'Failure/Jam': '#e74c3c'},
        title="Telemetry Matrix: Temp vs. Vibration Jams",
        labels={'temperature': 'Temperature (°C)', 'vibration': 'Vibration (mm/s)', 'status': 'System Status'},
        template="plotly_dark",
        opacity=0.8
    )
    fig_sensor.update_layout(
        paper_bgcolor='#1e293b', 
        plot_bgcolor='#1e293b',
        font_color='white', 
        title_x=0.5,
        xaxis=dict(gridcolor='#334155'), 
        yaxis=dict(gridcolor='#334155')
    )
    return fig_box, fig_bar, fig_priority_process

@app.callback(
    Output('live-time', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_time(n):
    return datetime.now().strftime(
        "System Time: %d-%m-%Y %H:%M:%S"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050)
