from nameko.rpc import rpc, ServiceRpc


class RpcResponderDemoService:
    name = "rpc_responder_demo_service"

    @rpc
    def hello(self, name):
        return "Hello, {}!".format(name)


class RpcCallerDemoService:
    name = "rpc_caller_demo_service"

    remote = ServiceRpc("rpc_responder_demo_service")

    @rpc
    def remote_hello(self, value="John Doe"):
        res = u"{}".format(value)
        return self.remote.hello(res)
