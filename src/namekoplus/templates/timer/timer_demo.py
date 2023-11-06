from nameko.timer import timer
from nameko_tracer import Tracer
from namekoplus import init_statsd, init_sentry


class Timer:

    name = 'timer'

    tracer = Tracer()
    sentry = init_sentry()
    statsd = init_statsd('statsd_prefix', 'statsd_host', 'statsd_port')

    @timer(interval=1)
    @statsd.timer('ping')
    def ping(self):
        # method executed every second
        print("pong")