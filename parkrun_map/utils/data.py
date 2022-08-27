import os
import re
from typing import Dict, Union
import urllib

import pandas as pd
import requests
from lxml import html

from . lookup import COUNTRY_LOOKUP


USER_AGENT = "Mozilla/4.0 (compatible; MSIE 6.0; Windows 98)"
PRETTY_TIME_REGEX = re.compile('^00:')

COURSE_FILEPATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'course_data.csv')
EVENT_SUMMARY_COLUMNS = ['event_name', 'country', 'run_count', 'personal_best']


def parse_fields(row: html.Element) -> Dict[str, Union[str, int]]:
    """
    Extract fields from a tr element of the table.
    The returned data dict should have one entry for each column in EVENT_SUMMARY_COLUMNS.

    Note: This method is sensitive to HTML layout
    """
    data_dict = {}
    field_elements = row.xpath('./td')

    for i, field in enumerate(field_elements):
        if i == 0:
            a = field.xpath('./a')[0]
            url = a.get('href')  # e.g. 'https://www.parkrun.org.uk/highburyfields/results'
            data_dict['event_name'] = url.split('/')[-2]
            top_level_domain = urllib.parse.urlparse(url).netloc
            domain_extension = top_level_domain.split('parkrun')[1]
            data_dict['country'] = COUNTRY_LOOKUP[domain_extension]  # e.g. 'UK'
        if i == 1:
            data_dict['run_count'] = int(field.text)  # e.g. 100
        if i == 4:
            raw_pb_time = field.xpath('./span')[0].text  # e.g. '00:19:55'
            data_dict['personal_best'] = PRETTY_TIME_REGEX.sub('', raw_pb_time)  # e.g. '19:55'

    return data_dict


def get_athlete_data(athlete_id: Union[str, int]) -> pd.DataFrame:
    """
    Visit the athlete page corresponding to the given athlete ID to extract their event summary data.

    :param athlete_id: int, the unique athlete ID, e.g. 1283894
    :return: DataFrame, containing event-summary data for that athlete
    """

    if isinstance(athlete_id, str):
        athlete_id = int(athlete_id.replace('A', ''))

    response = requests.get(f'https://www.parkrun.org.uk/parkrunner/{athlete_id}/', headers={'user-agent': USER_AGENT})
    html_tree = html.fromstring(response.text)
    event_summary_rows = html_tree.xpath('//h3[@id="event-summary"]/following-sibling::table/tbody/tr')  # note: sensitive to HTML layout

    data = []
    for es_row in event_summary_rows:
        field_data: dict = parse_fields(row=es_row)
        data.append(tuple([field_data[column] for column in EVENT_SUMMARY_COLUMNS]))

    return pd.DataFrame(data, columns=EVENT_SUMMARY_COLUMNS)


def get_course_data():
    df_courses = pd.read_csv(COURSE_FILEPATH)
    df_courses['latitude'] = round(df_courses['latitude'], 5)
    df_courses['longitude'] = round(df_courses['longitude'], 5)
    return df_courses


def get_athlete_and_course_data(athlete_id: Union[str, int]) -> pd.DataFrame:
    athlete_summary_data = get_athlete_data(athlete_id=athlete_id)
    course_data = get_course_data()

    # Check for missing courses
    missing_courses = set(athlete_summary_data['event_name']) - set(course_data['event_name'])
    if len(missing_courses) > 0:
        course_data = update_course_data(new_course_event_names=missing_courses)

    # Right join to enable showing missing parkruns
    df_merged = pd.merge(athlete_summary_data, course_data, on=['event_name', 'country'], how='right')
    df_merged.loc[pd.isnull(df_merged['run_count']), 'personal_best'] = 'N/A'
    df_merged.loc[pd.isnull(df_merged['run_count']), 'run_count'] = 0
    df_merged['run_count'] = df_merged['run_count'].astype(int)

    return df_merged
