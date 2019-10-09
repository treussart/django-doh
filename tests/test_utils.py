import unittest
from unittest.mock import Mock, MagicMock

import dns
from django.http import HttpResponse
from django.test import TestCase

from doh_server.constants import (
    DOH_CONTENT_TYPE
)
from doh_server.utils import (
    doh_b64_encode,
    doh_b64_decode,
    configure_logger,
    get_scheme,
    set_headers,
    extract_from_params,
)


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.request_mock = Mock()
        self.request_mock.is_secure.return_value = False
        self.request_mock.method = "GET"

        self.query = dns.message.make_query(qname="example.com", rdtype="A", want_dnssec=False)
        self.query_with_answer = dns.message.make_response(self.query)
        answer = Mock()
        answer.ttl = 1
        self.query_with_answer.answer.append(answer)
        self.query_with_answer.to_wire = MagicMock(return_value="wire format")

    def test_doh_b64_encode(self):
        assert doh_b64_encode(b"test") == "dGVzdA"
        assert doh_b64_encode(b"test==te&111%") == "dGVzdD09dGUmMTExJQ"
        with self.assertRaises(TypeError):
            doh_b64_encode(None)

    def test_doh_b64_decode(self):
        assert doh_b64_decode("dGVzdA") == b"test"
        assert doh_b64_decode("dGVzdD09dGUmMTExJQ") == b"test==te&111%"
        with self.assertRaises(TypeError):
            doh_b64_decode(None)

    def test_configure_loggers(self):
        logger = configure_logger()
        assert logger.level == 10
        assert logger.name == "root"

        logger = configure_logger("test")
        assert logger.level == 10
        assert logger.name == "test"

        logger = configure_logger("test", "INFO")
        assert logger.level == 20
        assert logger.name == "test"

        logger = configure_logger("test", "info")
        assert logger.level == 20
        assert logger.name == "test"

        with self.assertRaises(Exception):
            configure_logger("test", "test")

    def test_get_scheme(self):
        assert get_scheme(self.request_mock) == "http"
        self.request_mock.is_secure.return_value = True
        assert get_scheme(self.request_mock) == "https"

    def test_extract_from_params(self):
        param = "AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAAAgACAAEAAEAAA"
        assert str(extract_from_params(param).question[0]) == "s0.wp.com. IN AAAA"

        param = "AAABAAABAAAAAAABAnMwAndwA2NvbQAAHAABAAApEAAAAAAAAAgAAEAAEAAA"
        assert extract_from_params(param) is None

        param = "AQAAQDhAAMAAQAAAAAAAAthAAAAJDczODFmZDM2LTNiOTYtNDVmYS04MjQ2LWRkYzJkMmViYjQ2YQ==="
        assert extract_from_params(param) is None

        param = ""
        assert extract_from_params(param) is None


class TestUtilsWithDjango(TestCase):
    def setUp(self):
        self.request_mock = Mock()
        self.request_mock.is_secure.return_value = False
        self.request_mock.method = "GET"

        self.query = dns.message.make_query(qname="example.com", rdtype="A", want_dnssec=False)
        self.query_with_answer = dns.message.make_response(self.query)
        answer = Mock()
        answer.ttl = 1
        self.query_with_answer.answer.append(answer)
        self.query_with_answer.to_wire = MagicMock(return_value="wire format")

    def test_set_headers(self):
        response = HttpResponse("", status=200, content_type=DOH_CONTENT_TYPE, charset="utf-8")

        response = set_headers(self.request_mock, response, self.query)
        assert response["authority"] == ""
        assert response["method"] == "GET"
        assert response["scheme"] == "http"
        with self.assertRaises(KeyError):
            response["cache-control"]

        response = set_headers(self.request_mock, response, self.query_with_answer)
        assert response["authority"] == ""
        assert response["method"] == "GET"
        assert response["scheme"] == "http"
        assert response["cache-control"] == "max-age=1"

