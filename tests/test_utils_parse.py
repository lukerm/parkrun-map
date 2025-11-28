import os
import unittest
from unittest.mock import patch, Mock

from parkrun_map.utils.data import USER_AGENT
from parkrun_map.utils.parse import parse_event_coordinates


# TODO: convert to pytest
class TestGetAthleteData(unittest.TestCase):
    @patch('requests.get')
    def test_get_athlete_data(self, mock_requests_get):
        url_eg = "https://www.google.com/maps/d/u/0/embed?mid=1cul_pzUJgqSfRZpnwcTVfr6piNVNYV4&ehbc=2E312F"
        html_str_eg = f"""
        <html><body>
        <iframe src="{url_eg}" width="450" height="450"></iframe>
        </body></html>        
        """

        parent_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(parent_dir, 'data', 'course_data_cornwallpark.example.html'), 'r') as f:
            response_text = f.read().strip()

        self.assertEqual(response_text[:5], "<html")

        # Create a mock response
        mock_response = Mock()
        mock_response.text = response_text
        # Set up the mock requests.get to return our mock response
        mock_requests_get.return_value = mock_response

        # Call the function with test data
        coords = parse_event_coordinates(html_str=html_str_eg)

        # Assert that requests.get was called with the expected arguments
        expected_headers = {'user-agent': USER_AGENT}
        mock_requests_get.assert_called_once_with(url_eg, headers=expected_headers)

        # Verify the result has the expected structure
        self.assertAlmostEqual(coords[0], -36.89, delta=0.1)
        self.assertAlmostEqual(coords[1], 174.79, delta=0.1)


if __name__ == '__main__':
    unittest.main()
