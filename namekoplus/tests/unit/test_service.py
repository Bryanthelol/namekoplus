"""
Service unit testing best practice.
"""

from nameko.testing.services import worker_factory


def test_example_service():
    """
    Test example service.
    """
    # create worker with mock dependencies
    service = worker_factory(ServiceName)  # TODO replace ServiceName with the name of the service and import it

    # add side effects to the mock rpc dependency on the "remote" service
    service.remote.hello.side_effect = lambda name: "Hello, {}!".format(name)

    # test remote_hello business logic
    assert service.remote_hello("Bryant") == "Hello, Bryant!"
    service.remote.hello.assert_called_once_with("Bryant")