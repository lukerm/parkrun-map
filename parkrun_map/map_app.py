import argparse
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import pyarrow.parquet as pq
import s3fs

from dash.dependencies import Input, Output, State
from waitress import serve

from parkrun_map.utils.s3 import read_data_for_athlete_id


USE_S3 = False
PARQUET_TABLES_S3 = "lukerm-ds-open/parkrun/data/parquet"
PARQUET_TABLES_LOCAL = os.path.join(os.path.expanduser('~'), "parkrun-map", "data")
FIRST_ATHLETE_ID = 123
FIG_HEIGHT = 700


def get_athlete_data(athlete_id: str, show_missing: bool = False, show_parkruns: bool = True, show_juniors: bool = False) -> pd.DataFrame:
    # We must show at least one of usual parkruns and junior parkruns
    assert any([show_parkruns, show_juniors])

    # Get the athlete's entire history
    # TODO: Remove leading 'A' if present
    tables_location = PARQUET_TABLES_S3 if USE_S3 else PARQUET_TABLES_LOCAL
    athlete_data = read_data_for_athlete_id(athlete_id=int(athlete_id), parquet_table_location=os.path.join(tables_location, "athletes"), s3_mode=USE_S3)
    #course_data = get_courses_data(parquet_table_location=os.path.join(tables_location, "course_locations"), s3_mode=USE_S3)
    # Summarize by grouping by event
    grouped_by_event = athlete_data.groupby(['country', 'event_name'])
    athlete_data = grouped_by_event[['run_time']].agg(['count', 'min'])
    athlete_data.columns = athlete_data.columns.get_level_values(1)
    athlete_data = athlete_data.reset_index().rename(columns={'count': 'run_count', 'min': 'personal_best'})
    athlete_data = pd.merge(athlete_data, course_data, on=['event_name', 'country'], how='right')  # Join summary back onto course table (global variable)
    # Fill missing run counts with 0
    athlete_data.loc[pd.isnull(athlete_data['run_count']), 'personal_best'] = 'N/A'
    athlete_data.loc[pd.isnull(athlete_data['run_count']), 'run_count'] = 0

    if all([show_parkruns, show_juniors]):
        pass  # No filtering on usual / junior events
    elif show_parkruns:
        # Do not show junior events (only usual parkruns)
        athlete_data = athlete_data[athlete_data['event_name'].apply(lambda name: '-juniors' not in name)]
    elif show_juniors:
        # Filter only on junior events
        athlete_data = athlete_data[athlete_data['event_name'].apply(lambda name: '-juniors' in name)]

    if not show_missing:
        athlete_data = athlete_data[athlete_data['run_count'] > 0]

    athlete_data['marker_color'] = athlete_data['run_count'].apply(lambda count: '#D81919' if count == 0 else '#26903B')
    athlete_data['marker_opacity'] = athlete_data['run_count'].apply(lambda count: 0.33 if count == 0 else 1)

    return athlete_data


def get_course_data(parquet_table_location: str, s3_mode: bool = False) -> pd.DataFrame:
    course_data = pq.read_table(source=parquet_table_location, filesystem=s3fs.S3FileSystem() if s3_mode else None).to_pandas()
    return course_data


def get_graph(athlete_id, checkbox_options):

    # At least one of parkruns and junior parkruns must be selected
    if 'show_parkruns' not in checkbox_options and 'show_juniors' not in checkbox_options:
        raise dash.exceptions.PreventUpdate()

    athlete_data = get_athlete_data(
        athlete_id=athlete_id,
        show_missing='show_missing' in checkbox_options,
        show_parkruns='show_parkruns' in checkbox_options,
        show_juniors='show_juniors' in checkbox_options
    )
    if len(athlete_data) == 0:
        raise dash.exceptions.PreventUpdate()

    lat_center, lon_center = athlete_data.sort_values('run_count', ascending=False).iloc[0][['latitude', 'longitude']].values
    # These lines format the RHS of the data fields when they appear in the hover bubble
    athlete_data['run_count'] = athlete_data['run_count'].apply(lambda n: f' {int(n)}')
    athlete_data['personal_best'] = athlete_data['personal_best'].apply(lambda pb: f' {pb}')
    fig = px.scatter_mapbox(
        athlete_data.rename(columns={'run_count': 'Run count ', 'personal_best': 'Personal best '}),
        lat="latitude", lon="longitude",
        hover_name="event_name",
        hover_data={"Run count ": True, "Personal best ": True, "latitude": False, "longitude": False, "marker_color": False},
        color="marker_color",
        color_discrete_map='identity',
        zoom=10, height=FIG_HEIGHT,
        opacity=athlete_data['marker_opacity'].values
    )

    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(mapbox_center={'lat': lat_center, 'lon': lon_center})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(showlegend=False)

    return fig


course_data = get_course_data(parquet_table_location=os.path.join(PARQUET_TABLES_S3 if USE_S3 else PARQUET_TABLES_LOCAL, "course_locations"), s3_mode=USE_S3)

base_figure = px.scatter_mapbox(
        get_athlete_data(FIRST_ATHLETE_ID),
        lat="latitude", lon="longitude",
        hover_data={"run_count": False, "personal_best": False, "latitude": False, "longitude": False, "marker_color": False},
        # color="run_count",
        # color_continuous_scale=px.colors.sequential.Greens_r,
        # color_discrete_sequence=["green"],
        color_discrete_sequence=['#26903B'],  # shade of green
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
        ],
        value=['show_parkruns'],
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(id='map_wrapper', children=dcc.Graph(id='map', figure=base_figure, config={'displayModeBar': False})),
])


@map_app.callback(
    Output('map', 'figure'),
    [Input('athlete_id', 'value'), Input('checkboxes', 'value')]
)
def update_graph(athlete_id, checkbox_options):
    context = dash.callback_context
    if context.inputs['athlete_id.value'] is None:
        raise dash.exceptions.PreventUpdate()

    return get_graph(athlete_id=athlete_id, checkbox_options=checkbox_options)


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
        fig = get_graph(athlete_id=athlete_id, checkbox_options=checkbox_options)
        return html.Div(id='map', children=dcc.Graph(figure=fig, config={'displayModeBar': False}))
    else:
        raise dash.exceptions.PreventUpdate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', default=False)
    args = parser.parse_args()

    if args.debug:
        map_app.run_server(debug=True, use_reloader=True)
    else:
        serve(map_app.server)
