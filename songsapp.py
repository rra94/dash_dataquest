import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State, Event
import random

##############################################################
        #DATA MANIPULATION (model)
##############################################################
df= pd.read_csv("/Users/rra/Downloads/metacritic/top500_clean.csv")
df['userscore'] = df['userscore'].astype(float)
df['metascore'] = df['metascore'].astype(float)
df['releasedate']=pd.to_datetime(df['releasedate'], format='%b %d, %Y')
df['year']=df["releasedate"].dt.year
df['decade']=(df["year"]//10)*10
#cleaning Genre
df['genre'] = df['genre'].str.strip()
df['genre'] = df['genre'].str.replace("/", ",")
df['genre'] = df['genre'].str.split(",")
#year trend
df_linechart= df.groupby('year')        .agg({'album':'size', 'metascore':'mean', 'userscore':'mean'})        .sort_values(['year'], ascending=[True]).reset_index()
df_linechart.userscore=df_linechart.userscore*10
#table
df_table= df.groupby('artist').agg({'album':'size', 'metascore':'sum', 'userscore':'sum'})
#genrebubble
df2=(df['genre'].apply(lambda x: pd.Series(x)) .stack().reset_index(level=1, drop=True).to_frame('genre').join(df[['year', 'decade', 'userscore', 'metascore']], how='left') )
df_bubble=  df2.groupby('genre')        .agg({'year':'size', 'metascore':'mean', 'userscore':'mean'})             .sort_values(['year'], ascending=[False]).reset_index().head(15)
df2_decade=df2.groupby(['genre', 'decade']).agg({'year':'size'}) .sort_values(['decade'], ascending=[False]).reset_index()

##############################################################
        #DATA LAYOUT (view)
##############################################################

#gererate table
def generate_table(dataframe, max_rows=10):
    '''Given dataframe, return template generated using Dash components
    '''
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))],
        style={'width': '100%', 'display': 'inline-block', 'vertical-align': 'middle'}
    )

#generate bar chart
def  bar(results): 
    gen =results["points"][0]["text"]
    figure = go.Figure(
        data=[
            go.Bar(x=df2_decade[df2_decade.genre==gen].decade, y=df2_decade[df2_decade.genre==gen].year)
        ],
        layout=go.Layout(
            title="Decade populatrity of " + gen
        )
    )
    return figure

# Set up Dashboard and create layout
app = dash.Dash()

# Bootstrap CSS.
app.css.append_css({
    "external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"
})
# Bootstrap Javascript.
app.scripts.append_script({
    "external_url": "https://code.jquery.com/jquery-3.2.1.slim.min.js"
})
app.scripts.append_script({
    "external_url": "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js"
})

#define app layout
app.layout =  html.Div([ 
    html.Div([
        html.Div(
                    [
                        html.H1("Music Dashboard", className="text-center", id="heading")
                    ], className = "col-md-12"
                ),
        ],className="row"),

    html.Div(
        [ #dropdown and score
            html.Div([
                html.Div(
                    [
                        dcc.Dropdown(
                            options=[
                                {'label': 'userscore', 'value': 'userscore'},
                                {'label': 'metascore', 'value': 'metascore'},  
                            ],
                            id='score-dropdown'
                        )
                    ], className="col-md-12"),
                html.Div(
                    html.Table(id='datatable', className = "table col-md-12")
            ),
            ],className="col-md-6"),

            html.Div(
                [ #Line Chart
                    dcc.Graph(id='line-graph',
                        figure=go.Figure(
                            data = [ 
                                go.Scatter(
                                x = df_linechart.year,
                                y = df_linechart.userscore,
                                mode = 'lines',
                                name = 'user score'
                            ),
                            go.Scatter(
                                x = df_linechart.year,
                                y = df_linechart.metascore,
                                mode = 'lines',
                                name = 'meta score'
                            ),
                            ],
                            layout=go.Layout(title="Score trends")
                        )   
                              ),
                ], className = "col-md-6"
            ),
        ], className="row"),

    html.Div(
        [
            html.Div(
                [
                    dcc.Graph(id='bubble-chart',
                             figure=go.Figure(
                                 data=[
                                     go.Scatter(
                                        x=df_bubble.userscore,
                                        y=df_bubble.metascore,
                                        mode='markers',
                                        text=df_bubble.genre,
                                        
                                        marker=dict(
                                        color= random.sample(range(1,200),15),
                                        size=df_bubble.year,
                                        sizemode='area',
                                        sizeref=2.*max(df_bubble.year)/(40.**2),
                                        sizemin=4
                                        )
                                     )
                                 ],
                                 layout=go.Layout(title="Genre poularity")
                             )
                              
                              
                              )
                ], className = "col-md-6"
            ),
   html.Div(
                [
                    dcc.Graph(id='bar-chart',
                              style={'margin-top': '20'})
                ], className = "col-md-6"
            ),
        
        ], className="row"),

 ], className="container-fluid")

##############################################################
            #DATA CONTROL (CONTROLLER)
##############################################################
@app.callback(
    Output(component_id='datatable', component_property='children'),
    [Input(component_id='score-dropdown', component_property='value')]
)

def update_table(input_value):
    return generate_table(df_table.sort_values([input_value], ascending=[False]).reset_index())

@app.callback(
    Output(component_id='bar-chart', component_property='figure'),
    [Input(component_id='bubble-chart', component_property='hoverData')]
)

def update_graph(hoverData):
   return bar(hoverData)



if __name__ == '__main__':
    app.run_server(debug=True)
