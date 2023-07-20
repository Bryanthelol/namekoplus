import json
from nameko.web.handlers import http
from nameko_tracer import Tracer
from werkzeug.wrappers import Response
from namekoplus import init_statsd, init_sentry


class HttpDemoService:

    name = "http_demo_service"

    tracer = Tracer()
    sentry = init_sentry()
    statsd = init_statsd('statsd_prefix', 'statsd_host', 'statsd_port')

    @http("GET", "/broken")
    @statsd.timer('broken')
    def broken(self, request):
        raise ConnectionRefusedError()

    @http('GET', '/books/<string:uuid>')
    @statsd.timer('demo_get')
    def demo_get(self, request, uuid):
        data = {'id': uuid, 'title': 'The unbearable lightness of being',
                'author': 'Milan Kundera'}
        return Response(json.dumps({'book': data}),
                        mimetype='application/json')

    @http('POST', '/books')
    @statsd.timer('demo_post')
    def demo_post(self, request):
        return Response(json.dumps({'book': request.data.decode()}),
                        mimetype='application/json')
