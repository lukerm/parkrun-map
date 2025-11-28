import re
from typing import Tuple

import requests
from lxml import html


USER_AGENT = "Mozilla/4.0 (compatible; MSIE 6.0; Windows 98)"


def parse_event_coordinates(html_str: str) -> Tuple[float, float]:
    """
    Parse event coordinates from a Google My Maps HTML string.
    Returns the latitude and longitude of the 'Start' point as a representative location.

    :param html_str: HTML string containing the map data
    :return: Tuple of (latitude, longitude) as floats
    """
    html_tree = html.fromstring(html=html_str)
    location_url = html_tree.xpath('//iframe/@src')[0]

    response_location_page = requests.get(location_url, headers={'user-agent': USER_AGENT})

    pattern = '\[(-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+)\]'
    matches = re.findall(pattern, response_location_page.text)

    lat = sum([float(m[0]) for m in matches]) / len(matches)
    lon = sum([float(m[1]) for m in matches]) / len(matches)

    return lat, lon
