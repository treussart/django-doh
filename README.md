# Django-doh

Django-doh is a simple Django app to serve a DOH (DNS Over HTTPS) Proxy. It resolves DNS query on HTTP.

## Quick start

1. Install via pip:
```
pip install django-doh
```
2. Add `'doh_server'` to your `INSTALLED_APPS` setting like this:
```
INSTALLED_APPS = [
    ...
    'doh_server',
]
```
3. Include the `doh_server` URLconf in your project urls.py like this:
```
path('dns-query', include('doh_server.urls')),
```
4. Add the conf in your settings like this:
```
DOH_SERVER = {
    "RESOLVER": "internal",
    # "RESOLVER": "8.8.8.8",
    "AUTHORITY": "",
    "LOGGER_LEVEL": "DEBUG",
}
```
To use the local resolver on the server where you run Django, use `"internal"`.

## Implementation

### RFC 8484

* https://www.rfc-editor.org/rfc/rfc8484.txt

### Json implementation

* https://developers.cloudflare.com/1.1.1.1/dns-over-https/json-format/

## Use with Firefox

in `about:config` edit:

    network.trr.mode;3
    network.trr.uri;https://127.0.0.1/dns-query

For the URI, add your URI for your reverse proxy serving Django.

You can use Nginx as reverse proxy :

    events {
    }
    http {
        server {
            listen 443 ssl http2 default_server;
            location /dns-query {
                proxy_set_header Host $host;
                proxy_pass http://127.0.0.1:8000/dns-query;
            }
            ssl_certificate /etc/nginx/cert.pem;
            ssl_certificate_key /etc/nginx/key.pem;
        }
    }

## Test suite

Run using `tox`.

    tox --parallel

## Benchmark

Macbook Pro 2019
Processor 2,4 GHz Intel Core i5
Memory 8 GB 2133 MHz LPDDR3

Server Django and a reverse proxy Nginx in a Docker container.

`apib -c 100 -d 60 @benchmark_get_url.txt`

    HTTP/1.1
    Duration:             60.032 seconds
    Attempted requests:   7911
    Successful requests:  7911
    Non-200 results:      0
    Connections opened:   104
    Socket errors:        0

    Throughput:           131.780 requests/second
    Average latency:      734.647 milliseconds
    Minimum latency:      27.760 milliseconds
    Maximum latency:      9819.022 milliseconds
    Latency std. dev:     710.929 milliseconds
    50% latency:          606.548 milliseconds
    90% latency:          1360.734 milliseconds
    98% latency:          2845.927 milliseconds
    99% latency:          3612.085 milliseconds

    Client CPU average:    0%
    Client CPU max:        0%
    Client memory usage:    0%

    Total bytes sent:      1.15 megabytes
    Total bytes received:  2.44 megabytes
    Send bandwidth:        0.15 megabits / second
    Receive bandwidth:     0.33 megabits / second
