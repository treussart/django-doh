# Django-doh

Django-doh is a simple Django app to serve a DOH (DNS Over HTTPS) Proxy. It resolves DNS query on HTTP.

## Quick start

1. Install via pip:

    `pip install django-doh`

2. Add "doh_server" to your INSTALLED_APPS setting like this:
```
    INSTALLED_APPS = [
        ...
        'doh_server',
    ]
```

3. Include the polls URLconf in your project urls.py like this::
```
    from doh_server.views import doh_request
    path('dns-query', doh_request),
```

4. Add the conf in your settings like this::
```
    DOH_SERVER = {
        "RESOLVER": "internal",
        # "RESOLVER": "8.8.8.8",
        "AUTHORITY": "",
        "LOGGER_LEVEL": "DEBUG",
    }
```
For use local resolver set on the server who run Django use "internal".

## Implementation

### RFC 8484

* https://www.rfc-editor.org/rfc/rfc8484.txt

### Json implementation

* https://developers.cloudflare.com/1.1.1.1/dns-over-https/json-format/


## Use with Firefox

in about:config edit:
```
    network.trr.mode;3
    network.trr.uri;https://127.0.0.1/dns-query
```

For the URI, add your URI for your reverse proxy serving Django.

You can use Nginx as reverse proxy :
```
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
```


## Benchmark

Macbook Pro 2019
Processor 2,4 GHz Intel Core i5
Memory 8 GB 2133 MHz LPDDR3

`apib -c 100 -d 60 @benchmark_get_url.txt`
<pre>
HTTP/1.1
Duration:             60.013 seconds
Attempted requests:   6557
Successful requests:  6557
Non-200 results:      0
Connections opened:   100
Socket errors:        0

Throughput:           109.260 requests/second
Average latency:      907.811 milliseconds
Minimum latency:      52.990 milliseconds
Maximum latency:      30740.255 milliseconds
Latency std. dev:     1007.446 milliseconds
50% latency:          784.627 milliseconds
90% latency:          1409.109 milliseconds
98% latency:          1870.297 milliseconds
99% latency:          2083.914 milliseconds

Client CPU average:    0%
Client CPU max:        0%
Client memory usage:    0%

Total bytes sent:      0.97 megabytes
Total bytes received:  2.07 megabytes
Send bandwidth:        0.13 megabits / second
Receive bandwidth:     0.28 megabits / second
</pre>
