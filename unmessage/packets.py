from functools import wraps

import attr
from pyaxo import a2b

from . import elements
from . import errors
from .utils import raise_if_not


IV_LEN = 8
KEY_LEN = 32
ENC_KEY_LEN = 72
HASH_LEN = 32

LINESEP = '\n'


def raise_malformed(f):
    @wraps(f)
    def try_building(cls, data):
        try:
            return f(cls, data)
        except (AssertionError, IndexError, TypeError, ValueError):
            e = errors.MalformedPacketError(cls.__name__)
            indexed_lines = ['[{}]: {}'.format(index, line)
                             for index, line in enumerate(data.splitlines())]
            e.message = LINESEP.join([e.message] + indexed_lines)
            raise e
    return try_building


def is_valid_length(value, length):
        try:
            return isinstance(value, str) and len(a2b(value)) == length
        except TypeError:
            return False


def is_valid_non_empty(value):
        try:
            return isinstance(value, str) and len(a2b(value))
        except TypeError:
            return False


def is_valid_iv(value):
    return is_valid_length(value, IV_LEN)


def is_valid_key(value):
    return is_valid_length(value, KEY_LEN)


def is_valid_enc_key(value):
    return is_valid_length(value, ENC_KEY_LEN)


def is_valid_hash(value):
    return is_valid_length(value, HASH_LEN)


def is_valid_empty(value):
    return is_valid_length(value, 0)


@attr.s
class Packet(object):
    iv = attr.ib(validator=raise_if_not(is_valid_iv))
    iv_hash = attr.ib(validator=raise_if_not(is_valid_hash))

    @classmethod
    @raise_malformed
    def build(cls, data):
        return cls(*data.splitlines())


@attr.s
class IntroductionPacket(Packet):
    data = attr.ib(validator=raise_if_not(is_valid_non_empty))

    @classmethod
    @raise_malformed
    def build(cls, data):
        lines = data.splitlines()
        return cls(iv=lines[0],
                   iv_hash=lines[1],
                   data=data)

    def __str__(self):
        return self.data


@attr.s
class RegularPacket(Packet):
    payload_hash = attr.ib(validator=raise_if_not(is_valid_hash))
    handshake_key = attr.ib(validator=raise_if_not(is_valid_empty))
    payload = attr.ib(validator=raise_if_not(is_valid_non_empty))

    def __str__(self):
        return LINESEP.join([self.iv,
                             self.iv_hash,
                             self.payload_hash,
                             self.handshake_key,
                             self.payload])


@attr.s
class ReplyPacket(Packet):
    payload_hash = attr.ib(validator=raise_if_not(is_valid_hash))
    handshake_key = attr.ib(validator=raise_if_not(is_valid_enc_key))
    payload = attr.ib(validator=raise_if_not(is_valid_non_empty))

    def __str__(self):
        return LINESEP.join([self.iv,
                             self.iv_hash,
                             self.payload_hash,
                             self.handshake_key,
                             self.payload])


@attr.s
class RequestPacket(Packet):
    handshake_packet_hash = attr.ib(validator=raise_if_not(is_valid_hash))
    request_key = attr.ib(validator=raise_if_not(is_valid_key))
    handshake_packet = attr.ib(raise_if_not(is_valid_non_empty))

    def __str__(self):
        return LINESEP.join([self.iv,
                             self.iv_hash,
                             self.handshake_packet_hash,
                             self.request_key,
                             str(self.handshake_packet)])


@attr.s
class HandshakePacket(object):
    identity = attr.ib(validator=attr.validators.instance_of(str))
    identity_key = attr.ib(validator=raise_if_not(is_valid_key))
    handshake_key = attr.ib(validator=raise_if_not(is_valid_key))
    ratchet_key = attr.ib(validator=raise_if_not(is_valid_key))

    @classmethod
    @raise_malformed
    def build(cls, data):
        return cls(*data.splitlines())

    def __str__(self):
        return LINESEP.join([self.identity,
                             self.identity_key,
                             self.handshake_key,
                             self.ratchet_key])


@attr.s
class ElementPacket(object):
    type_ = attr.ib(validator=attr.validators.instance_of(str))
    payload = attr.ib(validator=attr.validators.instance_of(str))
    id_ = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(str)),
        default=attr.Factory(elements.get_random_id))
    part_num = attr.ib(default=1, convert=int)
    part_len = attr.ib(default=1, convert=int)

    @classmethod
    @raise_malformed
    def build(cls, data):
        lines = data.splitlines()
        return cls(type_=lines[0],
                   id_=lines[1],
                   part_num=lines[2],
                   part_len=lines[3],
                   payload=LINESEP.join(lines[4:]))

    def __str__(self):
        return LINESEP.join([self.type_,
                             self.id_,
                             str(self.part_num),
                             str(self.part_len),
                             self.payload])
