"""Tests for the crashes module."""

import json
import unittest
from unittest.mock import MagicMock, patch

import crashes


class TestFetchCrashes(unittest.TestCase):
    def _make_response(self, data: list, status_code: int = 200) -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = data
        mock_resp.raise_for_status.side_effect = None if status_code < 400 else Exception("HTTP Error")
        return mock_resp

    @patch("crashes.requests.get")
    def test_returns_records_on_success(self, mock_get):
        sample = [{"rd_no": "JA123", "crash_date": "2023-01-01", "injuries_total": "0"}]
        mock_get.return_value = self._make_response(sample)

        result = crashes.fetch_crashes(limit=1)

        self.assertEqual(result, sample)
        mock_get.assert_called_once()
        call_params = mock_get.call_args
        self.assertIn("$limit", call_params.kwargs.get("params", call_params.args[1] if len(call_params.args) > 1 else {}))

    @patch("crashes.requests.get")
    def test_passes_where_clause(self, mock_get):
        mock_get.return_value = self._make_response([])

        crashes.fetch_crashes(where="crash_year='2022'")

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["$where"], "crash_year='2022'")

    @patch("crashes.requests.get")
    def test_no_where_clause_by_default(self, mock_get):
        mock_get.return_value = self._make_response([])

        crashes.fetch_crashes()

        params = mock_get.call_args.kwargs["params"]
        self.assertNotIn("$where", params)

    @patch("crashes.requests.get")
    def test_raises_on_http_error(self, mock_get):
        import requests as req_lib

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.HTTPError("404 Not Found")
        mock_get.return_value = mock_resp

        with self.assertRaises(req_lib.HTTPError):
            crashes.fetch_crashes()

    @patch("crashes.requests.get")
    def test_raises_on_timeout(self, mock_get):
        import requests as req_lib

        mock_get.side_effect = req_lib.Timeout("Request timed out")

        with self.assertRaises(req_lib.Timeout):
            crashes.fetch_crashes()

    @patch("crashes.requests.get")
    def test_raises_on_connection_error(self, mock_get):
        import requests as req_lib

        mock_get.side_effect = req_lib.ConnectionError("Network unreachable")

        with self.assertRaises(req_lib.ConnectionError):
            crashes.fetch_crashes()

    @patch("crashes.requests.get")
    def test_pagination_offset(self, mock_get):
        mock_get.return_value = self._make_response([])

        crashes.fetch_crashes(limit=10, offset=50)

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["$limit"], 10)
        self.assertEqual(params["$offset"], 50)


if __name__ == "__main__":
    unittest.main()
