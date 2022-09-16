import socket
import threading
import socketserver
import time

class ThreadedUdpRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):

        data = self.request[0].strip()
        socket = self.request[1]
        client_addr = self.client_address[0]

        cur_thread = threading.current_thread()
        print(f'An UDP client(IP:{self.client_address[0]}, PORT:{self.client_address[1]}) is connected in {cur_thread}')

        response = bytes(f'{cur_thread.name}:{client_addr} wrote: {data}', 'utf-8')
        socket.sendto(response, self.client_address)

class ThreadedUdpServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

def udp_client(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        #sock.connect((ip, port))
        sock.sendto(bytes(message, 'utf-8'), (ip, port))
        response = str(sock.recv(1023), 'utf-8')
        print(f'received: {response}')

if __name__ == '__main__':
    host, port = 'localhost', 9998
    server = ThreadedUdpServer((host, port), ThreadedUdpRequestHandler)
    with server:
        ip, port = server.server_address
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        print('udp server loop running in thread', server_thread.name)
        for k in range(10):
            udp_client(ip, port, f'hello upd server {k}')
            time.sleep(0.1)
        server.shutdown()

