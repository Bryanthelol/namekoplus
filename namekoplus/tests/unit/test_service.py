"""
Service unit testing best practice.
"""

import pytest
from nameko.testing.services import worker_factory


@pytest.mark.parametrize(
    'value, expected',
    [
        ('John Doe', 'Hello, John Doe!'),
        ('', 'Hello, !'),
        ('Bryant', 'Hello, Bryant!'),
    ],
)
def test_example_service(value, expected):
    """
    Test example service.
    """
    # create worker with mock dependencies
    service = worker_factory(ServiceName)  # TODO replace ServiceName with the name of the service and import it

    # add side effects to the mock rpc dependency on the "remote" service
    service.remote.hello.side_effect = lambda name: "Hello, {}!".format(name)

    # test remote_hello business logic
    assert service.remote_hello(value) == expected
    service.remote.hello.assert_called_once_with(value)