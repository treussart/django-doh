import base64
import binascii
import json
import logging
from string import Template

from django.conf import settings
from django.http import HttpResponse, HttpRequest
from dns import message
from dns.message import Message

from doh_server.constants import (
    DOH_CONTENT_TYPE,
    DOH_JSON_CONTENT_TYPE,
    DOH_DNS_PARAM,
    DOH_DNS_JSON_PARAM,
)


def doh_b64_decode(s: str) -> bytes:
    """Base 64 urlsafe decode, add padding as needed.
    :param s: input base64 encoded string with potentially missing padding.
    :return: decodes bytes
    """
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def doh_b64_encode(s: bytes) -> str:
    """Base 64 urlsafe encode and remove padding.
    :param s: input bytes-like object to be encoded.
    :return: urlsafe base 64 encoded string.
    """
    return base64.urlsafe_b64encode(s).decode("utf-8").rstrip("=")


def configure_logger(name: str = "", level: str = "DEBUG"):
    """
    :param name: (optional) name of the logger, default: ''.
    :param level: (optional) level of logging, default: DEBUG.
    :return: a logger instance.
    """
    logging.basicConfig(format="%(asctime)s: %(levelname)8s: %(message)s")
    logger = logging.getLogger(name)
    level_name = level.upper()
    level = getattr(logging, level_name, None)
    if not isinstance(level, int):
        raise Exception("Invalid log level name : %s" % level_name)
    logger.setLevel(level)
    return logger


def get_scheme(request: HttpRequest) -> str:
    if request.is_secure():
        return "https"
    else:
        return "http"


def set_headers(
    request: HttpRequest, response: HttpResponse, query_response: Message
) -> HttpResponse:
    response["authority"] = settings.DOH_SERVER["AUTHORITY"]
    response["method"] = request.method
    response["scheme"] = get_scheme(request)
    if query_response.answer:
        ttl = min(r.ttl for r in query_response.answer)
        response["cache-control"] = "max-age=" + str(ttl)
    return response


def extract_from_params(dns_request: str) -> Message:
    logger = logging.getLogger("doh-server")
    try:
        dns_request_decoded = doh_b64_decode(dns_request)
        return message.from_wire(dns_request_decoded)
    except binascii.Error as ex:
        logger.info(str(ex))
    except Exception as ex:
        logger.exception(ex)


def get_name_and_type_from_dns_question(request: HttpRequest) -> Message:
    logger = logging.getLogger("doh-server")
    accept_header = request.headers.get("Accept")
    if request.method == "GET":
        if accept_header == DOH_JSON_CONTENT_TYPE:
            qname = request.GET.get(DOH_DNS_JSON_PARAM["name"], None)
            rdtype = request.GET.get(DOH_DNS_JSON_PARAM["type"], None)
            if qname and rdtype:
                return message.make_query(qname=qname, rdtype=rdtype)
        else:
            dns_request = request.GET.get(DOH_DNS_PARAM, None)
            if dns_request:
                return extract_from_params(dns_request)
    elif request.method == "POST" and request.content_type == DOH_CONTENT_TYPE:
        if request.body:
            try:
                return message.from_wire(request.body)
            except Exception as ex:
                logger.exception(str(ex))


def create_http_wire_response(request, query_response):
    logger = logging.getLogger("doh-server")
    logger.debug("[HTTP] " + str(request.method) + " " + str(request.content_type))
    if isinstance(query_response, Message):
        query_response.id = 0
        body = query_response.to_wire()
        response = HttpResponse(content=body, content_type=DOH_CONTENT_TYPE)
        response["content-length"] = str(len(body))
        return set_headers(request, response, query_response)
    else:
        return HttpResponse(status=200, content=query_response)


def create_http_json_response(request, query_response):
    logger = logging.getLogger("doh-server")
    logger.debug("[HTTP] " + str(request.method) + " " + str(request.content_type))
    response = HttpResponse(json.dumps({}), content_type=DOH_JSON_CONTENT_TYPE)
    if isinstance(query_response, Message):
        if query_response.answer:
            answers = []
            for answer in query_response.answer:
                answers.append(str(answer))
            with open(
                settings.BASE_DIR + "/doh_server/template.json", "r", encoding="UTF-8"
            ) as template:
                s = Template(template.read())
                response.content = json.dumps(
                    s.substitute(
                        data=json.dumps(answers),
                        name=query_response.answer[0].name,
                        type=query_response.answer[0].rdtype,
                        ttl=query_response.answer[0].ttl,
                    )
                )
        return set_headers(request, response, query_response)
    else:
        return HttpResponse(json.dumps({"content": str(query_response)}), status=200)
