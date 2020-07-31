import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import pyarrow.parquet as pq
import s3fs

from dash.dependencies import Input, Output

from parkrun_scrape.write_athlete_table import read_athlete_id

FIRST_ATHLETE_ID = 1283894


course_data = pq.read_table(source='lukerm-ds-open/parkrun/data/parquet/course_locations', filesystem=s3fs.S3FileSystem()).to_pandas()


def get_athlete_data(athlete_id: str) -> pd.DataFrame:
    # TODO: Remove leading 'A' if present
    athlete_data = read_athlete_id(athlete_id=int(athlete_id))
    athlete_data = athlete_data.groupby(['country', 'event_name'])[['gender']].count().reset_index().rename(columns={'gender': 'run_count'})
    athlete_data = pd.merge(athlete_data, course_data, on=['event_name', 'country'], how='left')
    athlete_data = athlete_data[~pd.isnull(athlete_data['run_count'])]
    return athlete_data


base_figure = px.scatter_mapbox(
        get_athlete_data(FIRST_ATHLETE_ID),
        lat="latitude", lon="longitude",
        hover_name="event_name",
        hover_data=["run_count"],
        # color="run_count",
        # color_continuous_scale=px.colors.sequential.Greens_r,
        # color_discrete_sequence=["green"],
        color_discrete_sequence=['magenta'],
        zoom=1, height=750,
        opacity=0
    )
base_figure.update_layout(mapbox_style="carto-positron")
base_figure.update_layout(mapbox_center={'lat': 51.42, 'lon': -0.33})
base_figure.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
base_figure.show()


map_app = dash.Dash()
map_app.layout = html.Div([
    dcc.Input(id='athlete_id', type='text', placeholder='Athlete ID e.g. 12345', debounce=True),
    dcc.Graph(id='map', figure=base_figure)
])


@map_app.callback(
    Output('map', 'figure'),
    [Input('athlete_id', 'value')]
)
def update_graph(athlete_id):
    if athlete_id is None:
        athlete_data = get_athlete_data(athlete_id=FIRST_ATHLETE_ID)
        fig = px.scatter_mapbox(athlete_data, lat="latitude", lon="longitude", zoom=1, height=750, opacity=0, hover_name=None, hover_data=None)
        fig.update_layout(hovermode=False)
    else:
        athlete_data = get_athlete_data(athlete_id=athlete_id)
        fig = px.scatter_mapbox(
            athlete_data,
            lat="latitude", lon="longitude",
            hover_name="event_name",
            hover_data=["run_count"],
            # color="run_count",
            # color_continuous_scale=px.colors.sequential.Greens_r,
            # color_discrete_sequence=["green"],
            color_discrete_sequence=['magenta'],
            zoom=10, height=750,
            opacity=1
        )

    fig.update_layout(mapbox_style="carto-positron")
    lat_center, lon_center = athlete_data.sort_values('run_count', ascending=False).iloc[0][['latitude', 'longitude']].values
    fig.update_layout(mapbox_center={'lat': lat_center, 'lon': lon_center})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.show()

    return fig


if __name__ == "__main__":
    map_app.run_server(debug=True, use_reloader=False)
