import pickle
import socket


# common_utils.py
BYTE_COUNT = 4

def encode(obj):
    return pickle.dumps(obj)
def decode(obj):
    return pickle.loads(obj)

def send_msg(sock, msg):
    """Send a message via the socket."""
    msg = add_msg_header(msg)
    sock.sendall(msg)


def send_udp_msg(sock, msg, ip, port):
    """Send a message via the socket."""
    msg = add_msg_header(msg)
    sock.sendto(msg, (ip, port))

def recv_msg(sock):
    """Receive a message via the socket."""

    # start by getting the header
    # (which is an int of length `BYTE_COUNT`).
    # The header tells the message size in bytes.
    raw_msglen = recvall(sock, BYTE_COUNT)

    if not raw_msglen:
        return None
    # Then retrieve a message of length `raw_msglen`
    # this will be the actual message
    msglen = len_frombytes(raw_msglen)
    return recvall(sock, msglen)

async def recv_async(receiver):
    raw_msglen = await receiver.read(BYTE_COUNT)
    if not raw_msglen:
        return None
    msglen = len_frombytes(raw_msglen)
    return await receiver.read(msglen)

def recvall(sock, length):
    """Get a message of a certain length from the socket stream"""
    data = bytearray()
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def add_msg_header(msg):
    return len_inbytes(msg) + msg

def len_inbytes(msg):
    return len(msg).to_bytes(BYTE_COUNT, byteorder='big')

def len_frombytes(bmsg):
    return int.from_bytes(bmsg, byteorder='big')