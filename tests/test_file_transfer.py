import pytest
from twisted.internet.defer import Deferred

from unmessage.peer import b2a
from pyaxo import hash_

from .utils import remove_file


@pytest.inlineCallbacks
def test_send_file(out_contents, out_path, in_path, peers,
                   callback_side_effect):
    peer_a, peer_b, conv_a, conv_b = yield peers

    out_hash = hash_(out_contents)

    d_req_in = Deferred()
    conv_b.ui.notify_in_file_request = callback_side_effect(d_req_in)
    d_file_out = Deferred()
    conv_a.ui.notify_finished_out_file = callback_side_effect(d_file_out)
    d_file_in = Deferred()
    conv_b.ui.notify_finished_in_file = callback_side_effect(d_file_in)

    yield peer_a.send_file(peer_b.name, out_path)
    yield d_req_in
    yield peer_b.accept_file(peer_a.name, b2a(out_hash), in_path)
    yield d_file_out
    yield d_file_in

    in_contents = open(in_path, 'r').read()
    assert in_contents == out_contents
    assert hash_(in_contents) == out_hash


@pytest.fixture
def out_contents():
    return 'contents'


@pytest.fixture
def out_path():
    return '/tmp/unmessage-out-file.txt'


@pytest.fixture
def in_path():
    return '/tmp/unmessage-in-file.txt'


@pytest.fixture(autouse=True)
def setup_teardown(out_contents, out_path, in_path):
    open(out_path, 'w').write(out_contents)
    remove_file(in_path)
    yield
    remove_file(out_path)
    remove_file(in_path)
