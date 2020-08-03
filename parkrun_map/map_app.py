import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import pyarrow.parquet as pq
import s3fs

from dash.dependencies import Input, Output

from parkrun_map.utils.s3 import read_data_for_athlete_id


ATHLETE_TABLE_S3 = "lukerm-ds-open/parkrun/data/parquet/athletes"
ATHLETE_TABLE_LOCAL = os.path.join(os.path.expanduser('~'), "parkrun-map", "data")
FIRST_ATHLETE_ID = 1283894
FIG_HEIGHT = 700


course_data = pq.read_table(source='lukerm-ds-open/parkrun/data/parquet/course_locations', filesystem=s3fs.S3FileSystem()).to_pandas()


def get_athlete_data(athlete_id: str, show_missing: bool = False, show_juniors: bool = False) -> pd.DataFrame:
    # TODO: Remove leading 'A' if present
    athlete_data = read_data_for_athlete_id(athlete_id=int(athlete_id), parquet_table_location=ATHLETE_TABLE_LOCAL, s3_mode=False)
    athlete_data = athlete_data.groupby(['country', 'event_name'])[['gender']].count().reset_index().rename(columns={'gender': 'run_count'})
    athlete_data = pd.merge(athlete_data, course_data, on=['event_name', 'country'], how='right')
    athlete_data.loc[pd.isnull(athlete_data['run_count']), 'run_count'] = 0  # Fill missing run counts with 0

    if not show_missing:
        athlete_data = athlete_data[athlete_data['run_count'] > 0]
    elif not show_juniors:
        athlete_data = athlete_data[athlete_data['event_name'].apply(lambda name: '-juniors' not in name)]

    athlete_data['marker_color'] = athlete_data['run_count'].apply(lambda count: '#D81919' if count == 0 else '#26903B')
    athlete_data['marker_opacity'] = athlete_data['run_count'].apply(lambda count: 0.33 if count == 0 else 1)

    return athlete_data


base_figure = px.scatter_mapbox(
        get_athlete_data(FIRST_ATHLETE_ID),
        lat="latitude", lon="longitude",
        hover_name="event_name",
        hover_data=["run_count"],
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
    dcc.Input(id='athlete_id', type='text', placeholder='Athlete ID e.g. 12345', debounce=True),
    dcc.Checklist(
        id='checkboxes',
        options=[
            {'label': 'Show missing', 'value': 'show_missing'},
            {'label': 'Show Junior parkruns', 'value': 'show_juniors'},
        ],
        value=[],
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='map', figure=base_figure, config={'displayModeBar': False})
])


@map_app.callback(
    Output('map', 'figure'),
    [Input('athlete_id', 'value'), Input('checkboxes', 'value')]
)
def update_graph(athlete_id, checkbox_options):
    if athlete_id is None:
        athlete_data = get_athlete_data(athlete_id=FIRST_ATHLETE_ID)
        fig = px.scatter_mapbox(athlete_data, lat="latitude", lon="longitude", zoom=1, height=FIG_HEIGHT, opacity=0, hover_name=None, hover_data=None)
        fig.update_layout(hovermode=False)
    else:
        athlete_data = get_athlete_data(athlete_id=athlete_id, show_missing='show_missing' in checkbox_options, show_juniors='show_juniors' in checkbox_options)
        fig = px.scatter_mapbox(
            athlete_data,
            lat="latitude", lon="longitude",
            hover_name="event_name",
            hover_data={"run_count": True, "latitude": False, "longitude": False, "marker_color": False},
            color="marker_color",
            zoom=10, height=FIG_HEIGHT,
            opacity=athlete_data['marker_opacity'].values
        )

    fig.update_layout(mapbox_style="carto-positron")
    lat_center, lon_center = athlete_data.sort_values('run_count', ascending=False).iloc[0][['latitude', 'longitude']].values
    fig.update_layout(mapbox_center={'lat': lat_center, 'lon': lon_center})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(showlegend=False)

    return fig


if __name__ == "__main__":
    map_app.run_server(debug=True, use_reloader=False)
