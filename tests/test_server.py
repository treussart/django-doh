import dns
from django.test import TestCase, Client
from django.urls import reverse
from dns import message
from doh_server.constants import DOH_CONTENT_TYPE, DOH_JSON_CONTENT_TYPE
from doh_server.utils import doh_b64_encode


class GetTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_url_without_http_accept(self):
        response = self.client.get(reverse("doh_request"))
        self.assertEqual(response.status_code, 400)

    def test_url_without_param(self):
        response = self.client.get(reverse("doh_request"), HTTP_ACCEPT=DOH_CONTENT_TYPE)
        self.assertEqual(response.status_code, 400)

    def test_url_without_param_json(self):
        response = self.client.get(
            reverse("doh_request"), HTTP_ACCEPT=DOH_JSON_CONTENT_TYPE
        )
        self.assertEqual(response.status_code, 400)

    def test_url_with_param_not_base64(self):
        response = self.client.get(
            reverse("doh_request"), {"dns": "test.com"}, HTTP_ACCEPT=DOH_CONTENT_TYPE
        )
        self.assertEqual(response.status_code, 400)

    def test_timeout_dns_request(self):
        with self.settings(DOH_SERVER={"RESOLVER": "10.13.23.45", "AUTHORITY": ""}):
            message = dns.message.make_query(qname="treussart.com", rdtype="A")
            message.id = 0
            response = self.client.post(
                reverse("doh_request"),
                HTTP_ACCEPT=DOH_CONTENT_TYPE,
                content_type=DOH_CONTENT_TYPE,
                data=message.to_wire(),
            )
            self.assertEqual(response.status_code, 200)
            message_content = dns.message.from_wire(response.content)
            self.assertFalse(message_content.answer)
            self.assertEqual(message_content.rcode(), 2)


class PostTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_url_without_message(self):
        response = self.client.post(reverse("doh_request"))
        self.assertEqual(response.status_code, 400)

    def test_url_without_content_type(self):
        message = dns.message.make_query(qname="test.local", rdtype="A")
        response = self.client.post(reverse("doh_request"), content_type="application/text", data=message.to_wire())
        self.assertEqual(response.status_code, 400)

    def test_url_without_param(self):
        response = self.client.post(
            reverse("doh_request"),
            HTTP_ACCEPT=DOH_CONTENT_TYPE,
            content_type=DOH_CONTENT_TYPE,
        )
        self.assertEqual(response.status_code, 400)

    def test_url_with_param_nx_domain(self):
        message = dns.message.make_query(qname="test.local", rdtype="A")
        response = self.client.post(
            reverse("doh_request"),
            HTTP_ACCEPT=DOH_CONTENT_TYPE,
            content_type=DOH_CONTENT_TYPE,
            data=message.to_wire(),
        )
        self.assertEqual(response.status_code, 200)
        message_content = dns.message.from_wire(response.content)
        self.assertEqual(message_content.rcode(), 3)
        self.assertFalse(message_content.answer)

    def test_url_with_param(self):
        message = dns.message.make_query(qname="treussart.com", rdtype="A")
        response = self.client.post(
            reverse("doh_request"),
            HTTP_ACCEPT=DOH_CONTENT_TYPE,
            content_type=DOH_CONTENT_TYPE,
            data=message.to_wire(),
        )
        self.assertEqual(response.status_code, 200)
        message_content = dns.message.from_wire(response.content)
        self.assertEqual(message_content.rcode(), 0)
        self.assertIn("treussart.com.", str(message_content.answer[0]))


class GetTestCaseDNSMessage(TestCase):
    def setUp(self):
        self.client = Client()

    def test_with_dns_answer(self):
        q = dns.message.make_query(qname="treussart.com", rdtype="A")
        data = q.to_wire()
        for resolver in ["internal", "8.8.8.8"]:
            with self.subTest(resolver=resolver):
                with self.settings(DOH_SERVER={"RESOLVER": resolver, "AUTHORITY": ""}):
                    response = self.client.get(
                        reverse("doh_request"),
                        {"dns": doh_b64_encode(data)},
                        HTTP_ACCEPT=DOH_CONTENT_TYPE,
                    )
                    self.assertEqual(response.status_code, 200)
                    message_content = message.from_wire(response.content)
                    self.assertEqual(message_content.rcode(), 0)
                    self.assertIn("treussart.com.", str(message_content.answer[0]))
                    self.assertIn(" IN A ", str(message_content.answer[0]))

    def test_without_dns_answer(self):
        q = dns.message.make_query(qname="test.local", rdtype="A")
        data = q.to_wire()
        for resolver in ["internal", "8.8.8.8"]:
            with self.subTest(resolver=resolver):
                with self.settings(DOH_SERVER={"RESOLVER": resolver, "AUTHORITY": ""}):
                    response = self.client.get(
                        reverse("doh_request"),
                        {"dns": doh_b64_encode(data)},
                        HTTP_ACCEPT=DOH_CONTENT_TYPE,
                    )
                    self.assertEqual(response.status_code, 200)
                    message_content = dns.message.from_wire(response.content)
                    self.assertEqual(message_content.rcode(), 3)
                    self.assertFalse(message_content.answer)


class GetTestCaseDNSJson(TestCase):
    def setUp(self):
        self.client = Client()

    def test_ok_with_dns_answer(self):
        for resolver in ["internal", "8.8.8.8"]:
            with self.subTest(resolver=resolver):
                with self.settings(DOH_SERVER={"RESOLVER": resolver, "AUTHORITY": ""}):
                    response = self.client.get(
                        reverse("doh_request"),
                        {"name": "treussart.com", "type": "A"},
                        HTTP_ACCEPT=DOH_JSON_CONTENT_TYPE,
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("treussart.com.", response.content.decode("UTF-8"))

    def test_ok_without_dns_answer(self):
        for resolver in ["internal", "8.8.8.8"]:
            with self.subTest(resolver=resolver):
                with self.settings(DOH_SERVER={"RESOLVER": resolver, "AUTHORITY": ""}):
                    response = self.client.get(
                        reverse("doh_request"),
                        {"name": "not_works", "type": "A"},
                        HTTP_ACCEPT=DOH_JSON_CONTENT_TYPE,
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual("{}", response.content.decode("UTF-8"))
