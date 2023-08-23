import argparse
from math import sqrt
from string import ascii_lowercase
from typing import List

import dash
from dash import dcc
from dash import html
import plotly.express as px
import plotly.graph_objects as go

from dash.dependencies import Input, Output, State
from waitress import serve

from parkrun_map.utils.data import get_athlete_and_course_data


FIG_HEIGHT = 700
# colours
COLOUR_COMPLETE = '#5D3A9B'  # purple
COLOUR_MISSING = '#E66100'  # orange


def get_graph(athlete_id, checkbox_options):

    # At least one of parkruns and junior parkruns must be selected
    if 'show_parkruns' not in checkbox_options and 'show_juniors' not in checkbox_options:
        raise dash.exceptions.PreventUpdate()

    athlete_data = get_athlete_and_course_data(athlete_id=athlete_id)

    # Filtering based on checked boxes
    show_missing = 'show_missing' in checkbox_options
    show_parkruns = 'show_parkruns' in checkbox_options
    show_juniors = 'show_juniors' in checkbox_options
    az_mode = 'az_mode' in checkbox_options
    if all([show_parkruns, show_juniors]):
        pass  # No filtering on usual / junior events
    elif show_parkruns:
        # Do not show junior events (only usual parkruns)
        athlete_data = athlete_data[athlete_data['event_name'].apply(lambda name: '-juniors' not in name)]
    elif show_juniors:
        # Filter only on junior events
        athlete_data = athlete_data[athlete_data['event_name'].apply(lambda name: '-juniors' in name)]

    athlete_data['event_title_pretty'] = athlete_data['event_title'].apply(
        lambda title: title.replace('parkrun', '').replace('junior', 'Juniors').replace(' ,', ',').strip()
    )
    athlete_data['first_letter'] = athlete_data['event_title_pretty'].apply(lambda title: title[0].lower())
    acquired_letters = sorted(list(set(athlete_data[athlete_data['run_count'] > 0]['first_letter'])))

    if not show_missing:
        athlete_data = athlete_data[athlete_data['run_count'] > 0]
    elif az_mode:
        missing_letters = list(set(list(ascii_lowercase)) - set(acquired_letters))
        athlete_data = athlete_data[(athlete_data['run_count'] > 0) | (athlete_data['first_letter'].isin(missing_letters))]

    # Extra tweaks for prettiness
    athlete_data['marker_color'] = athlete_data['run_count'].apply(lambda count: COLOUR_MISSING if count == 0 else COLOUR_COMPLETE)
    athlete_data['marker_opacity'] = athlete_data['run_count'].apply(lambda count: 0.33 if count == 0 else 1)

    if len(athlete_data) == 0:
        raise dash.exceptions.PreventUpdate()

    lat_center, lon_center = athlete_data.sort_values('run_count', ascending=False).iloc[0][['latitude', 'longitude']].values
    athlete_data['distance'] = athlete_data.apply(lambda row: sqrt((row['latitude'] - lat_center)**2 + (row['longitude'] - lon_center)**2), axis=1)
    athlete_data_complete = athlete_data[athlete_data['run_count'] > 0]
    athlete_data_missing = athlete_data[athlete_data['run_count'] == 0]
    if az_mode:
        athlete_data_nearest = athlete_data_missing.sort_values(by='distance', ascending=True).groupby('first_letter').head(1)

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        customdata=athlete_data_complete,
        lat=athlete_data_complete['latitude'],
        lon=athlete_data_complete['longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=8,
            color=COLOUR_COMPLETE,
            opacity=1
        ),
        text=athlete_data_complete['event_title_pretty'],
        hovertemplate='<b>%{customdata[7]}</b><br><br>Run count = %{customdata[2]:.0f}<br>Personal best = %{customdata[3]}<extra></extra>'
    ))

    if len(athlete_data_missing) > 0:
        fig.add_trace(go.Scattermapbox(
            lat=athlete_data_missing['latitude'],
            lon=athlete_data_missing['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=6,
                color=COLOUR_MISSING,
                opacity=0.6
            ),
            text=athlete_data_missing['event_title_pretty'],
            hoverinfo='text',
        ))

    if az_mode and len(athlete_data_nearest) > 0:
        fig.add_trace(go.Scattermapbox(
            lat=athlete_data_nearest['latitude'],
            lon=athlete_data_nearest['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=12,
                color=COLOUR_MISSING,
                opacity=1,
            ),
            text=athlete_data_nearest['event_title_pretty'],
            hoverinfo='text',
        ))

    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(mapbox_center={'lat': lat_center, 'lon': lon_center})
    fig.update_layout(mapbox_zoom=10)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(showlegend=False)
    fig.update_layout(height=FIG_HEIGHT)

    return fig, acquired_letters


base_figure = px.scatter_mapbox(
        get_athlete_and_course_data(123),
        lat="latitude", lon="longitude",
        hover_data={"run_count": False, "personal_best": False, "latitude": False, "longitude": False},
        color_discrete_sequence=[COLOUR_COMPLETE],
        zoom=1, height=FIG_HEIGHT,
        opacity=0
    )
base_figure.update_layout(mapbox_style="carto-positron")
base_figure.update_layout(mapbox_center={'lat': 51.42, 'lon': -0.33})
base_figure.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
base_figure.update_layout(showlegend=False)


map_app = dash.Dash()
map_app.layout = html.Div([
    dcc.Input(id='athlete_id', type='text', placeholder='Athlete ID e.g. 123', debounce=True),
    dcc.Checklist(
        id='checkboxes',
        options=[
            {'label': 'Show parkrun events', 'value': 'show_parkruns'},
            {'label': 'Show junior events', 'value': 'show_juniors'},
            {'label': 'Show missing events', 'value': 'show_missing'},
            {'label': 'A-Z mode', 'value': 'az_mode'},
        ],
        value=['show_parkruns'],
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(
        id='letters',
        children=[html.B(letter.upper(), style={'color': COLOUR_MISSING}, id=f'letter_{letter}') for letter in ascii_lowercase] +
                 [html.B(f' (0 / 26)', style={'color': COLOUR_COMPLETE}, id='letter_total')],
        style={'display': 'none'},
    ),
    html.Div(id='map_wrapper', children=dcc.Graph(id='map', figure=base_figure, config={'displayModeBar': False})),
    dcc.Store(id='az_store', data=[])
])


@map_app.callback(
    [
        Output('map', 'figure'),
        Output('az_store', 'data'),
        Output('letters', 'style'),
    ],
    [Input('athlete_id', 'value'), Input('checkboxes', 'value')]
)
def update_graph(athlete_id, checkbox_options):
    context = dash.callback_context
    if context.inputs['athlete_id.value'] is None:
        raise dash.exceptions.PreventUpdate()

    letters_display = {'display': 'block'} if 'az_mode' in checkbox_options else {'display': 'none'}
    fig, acquired_letters = get_graph(athlete_id=athlete_id, checkbox_options=checkbox_options)
    return fig, acquired_letters, letters_display


# Note: this callback is only needed to reload the map after the first load.
#       Needed because sometimes the map centres on the wrong location FOR THE FIRST LOAD ONLY!
#       This callback will only be used once during the runtime of the browser session (map_wrapper is overwritten)
@map_app.callback(
    Output('map_wrapper', 'children'),
    [Input('map', 'figure')],
    [State('athlete_id', 'value'), State('checkboxes', 'value')],
)
def reload_map(_map, athlete_id, checkbox_options):
    if athlete_id is not None:
        fig, _ = get_graph(athlete_id=athlete_id, checkbox_options=checkbox_options)
        return html.Div(id='map', children=dcc.Graph(figure=fig, config={'displayModeBar': False}))
    else:
        raise dash.exceptions.PreventUpdate()


@map_app.callback(
    [Output(f'letter_{letter}', 'style') for letter in ascii_lowercase] + [Output('letter_total', 'children')],
    [Input('az_store', 'data')]
)
def update_acquired_letter(acquired_letters: List[str]):
    return [
        {'color': COLOUR_COMPLETE} if letter in acquired_letters else {'color': COLOUR_MISSING}
        for letter in ascii_lowercase
    ] + [f' ({len(acquired_letters)} / 26)']


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', default=False)
    args = parser.parse_args()

    if args.debug:
        map_app.run_server(debug=True, use_reloader=True)
    else:
        serve(map_app.server)
