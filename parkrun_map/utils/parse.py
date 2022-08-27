import re
from typing import Tuple

import requests
from lxml import html


USER_AGENT = "Mozilla/4.0 (compatible; MSIE 6.0; Windows 98)"


def parse_event_coordinates(html_str: str) -> Tuple[float, float]:
    html_tree = html.fromstring(html=html_str)
    location_url = html_tree.xpath('//iframe/@src')[0]

    response_location_page = requests.get(location_url, headers={'user-agent': USER_AGENT})
    html_tree = html.fromstring(response_location_page.text)
    main_script = html_tree.xpath('//script')[0]
    script_body = main_script.text

    point_markers = re.findall('\[(-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+)\]', script_body)
    lat_str, lon_str = point_markers[0]
    return float(lat_str), float(lon_str)
