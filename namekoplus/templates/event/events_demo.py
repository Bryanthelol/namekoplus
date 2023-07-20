from nameko.events import EventDispatcher, event_handler
from nameko.rpc import rpc
from nameko_tracer import Tracer
from namekoplus import init_statsd, init_sentry


class EventPublisherService:

    name = "publisher_service"

    tracer = Tracer()
    sentry = init_sentry()
    statsd = init_statsd('statsd_prefix', 'statsd_host', 'statsd_port')

    dispatch = EventDispatcher()

    @rpc
    @statsd.timer('publish')
    def publish(self, event_type, payload):
        self.dispatch(event_type, payload)


class AnEventListenerService:

    name = "an_event_listener_service"

    tracer = Tracer()
    sentry = init_sentry()
    statsd = init_statsd('statsd_prefix', 'statsd_host', 'statsd_port')

    @event_handler("publisher_service", "an_event")
    @statsd.timer('consume_an_event')
    def consume_an_event(self, payload):
        print("service {} received:".format(self.name), payload)


class AnotherEventListenerService:

    name = "another_event_listener_service"

    tracer = Tracer()
    sentry = init_sentry()
    statsd = init_statsd('statsd_prefix', 'statsd_host', 'statsd_port')

    @event_handler("publisher_service", "another_event")
    @statsd.timer('consume_another_event')
    def consume_another_event(self, payload):
        print("service {} received:".format(self.name), payload)


class ListenBothEventsService:

    name = "listen_both_events_service"

    tracer = Tracer()
    sentry = init_sentry()
    statsd = init_statsd('statsd_prefix', 'statsd_host', 'statsd_port')

    @event_handler("publisher_service", "an_event")
    @statsd.timer('consume_an_event')
    def consume_an_event(self, payload):
        print("service {} received:".format(self.name), payload)

    @event_handler("publisher_service", "another_event")
    @statsd.timer('consume_another_event')
    def consume_another_event(self, payload):
        print("service {} received:".format(self.name), payload)
