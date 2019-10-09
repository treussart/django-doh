import unittest

import dns
from dns.message import Message

from doh_server.dns_resolver import DNSResolverClient


class TestDNSResolver(unittest.TestCase):
    def setUp(self):
        self.resolver_internal = DNSResolverClient()
        self.resolver_external = DNSResolverClient("8.8.8.8")
        self.resolver_not_exist = DNSResolverClient("10.13.23.45")
        self.query_ok = dns.message.make_query(
            qname="example.com", rdtype="A", want_dnssec=False
        )
        self.query_ok.id = 0
        self.query_not_ok = dns.message.make_query(
            qname="qname", rdtype="A", want_dnssec=False
        )
        self.query_not_ok.id = 0

    def test_dns_resolver_internal_no_answer(self):
        result_msg = self.resolver_internal.resolve(self.query_not_ok)
        assert isinstance(result_msg, Message)
        assert len(result_msg.answer) == 0
        assert result_msg.rcode() == 3
        assert self.resolver_internal.name_server != "8.8.8.8"

    def test_dns_resolver_internal_answer(self):
        result_msg = self.resolver_internal.resolve(self.query_ok)
        assert isinstance(result_msg, Message)
        assert len(result_msg.answer) == 1
        assert result_msg.rcode() == 0
        assert self.resolver_internal.name_server != "8.8.8.8"

    def test_dns_resolver_external_no_answer(self):
        result_msg = self.resolver_external.resolve(self.query_not_ok)
        assert isinstance(result_msg, Message)
        assert len(result_msg.answer) == 0
        assert result_msg.rcode() == 3
        assert self.resolver_external.name_server == "8.8.8.8"

    def test_dns_resolver_external_answer(self):
        result_msg = self.resolver_external.resolve(self.query_ok)
        assert isinstance(result_msg, Message)
        assert len(result_msg.answer) == 1
        assert result_msg.rcode() == 0
        assert self.resolver_external.name_server == "8.8.8.8"

    def test_dns_resolver_not_exist(self):
        result_msg = self.resolver_not_exist.resolve(self.query_not_ok)
        assert result_msg == 0


if __name__ == "__main__":
    unittest.main()
