from nameko.rpc import rpc, ServiceRpc
from nameko_tracer import Tracer
from namekoplus import init_statsd, init_sentry


class RpcResponderDemoService:
    name = "rpc_responder_demo_service"

    tracer = Tracer()
    sentry = init_sentry()
    statsd = init_statsd('statsd_prefix', 'statsd_host', 'statsd_port')

    @rpc
    @statsd.timer('hello')
    def hello(self, name):
        return "Hello, {}!".format(name)


class RpcCallerDemoService:
    name = "rpc_caller_demo_service"

    remote = ServiceRpc("rpc_responder_demo_service")

    sentry = init_sentry()
    statsd = init_statsd('statsd_prefix', 'statsd_host', 'statsd_port')

    @rpc
    @statsd.timer('remote_hello')
    def remote_hello(self, value="John Doe"):
        res = u"{}".format(value)
        return self.remote.hello(res)
