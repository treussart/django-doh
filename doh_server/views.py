import concurrent.futures

import dns
from django.conf import settings
from django.http import HttpResponseNotAllowed, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from dns import rcode
from dns.message import Message

from doh_server.constants import DOH_CONTENT_TYPE, DOH_JSON_CONTENT_TYPE
from doh_server.dns_resolver import DNSResolverClient
from doh_server.utils import (
    configure_logger,
    get_name_and_type_from_dns_question,
    create_http_wire_response,
    create_http_json_response,
)

logger = configure_logger("doh-server", level=settings.DOH_SERVER["LOGGER_LEVEL"])


@csrf_exempt
@require_http_methods(["GET", "POST"])
def doh_request(request):
    resolver_dns = DNSResolverClient(settings.DOH_SERVER["RESOLVER"])
    accept_header = request.headers.get("Accept")
    message = get_name_and_type_from_dns_question(request)
    if not message:
        return HttpResponseBadRequest()
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(resolver_dns.resolve, message)
            query_response = future.result()
        if isinstance(query_response, Message):
            if query_response.answer:
                logger.debug("[DNS] " + str(query_response.answer[0]))
            else:
                logger.debug("[DNS] " + str(query_response.question[0]))
        else:
            logger.warning("[DNS] Timeout on " + resolver_dns.name_server)
            query_response = dns.message.make_response(message)
            query_response.set_rcode(rcode.SERVFAIL)
    except Exception as ex:
        logger.exception(str(ex))
        return HttpResponseBadRequest()
    if request.method == "GET" and accept_header == DOH_JSON_CONTENT_TYPE:
        return create_http_json_response(request, query_response)
    else:
        return create_http_wire_response(request, query_response)
