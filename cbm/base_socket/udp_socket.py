############################################################################
# Python Module for UDP Socket Programming
# 미완성
############################################################################
# Main Features:
#    1. Multi-Threaded UDP Socket Server Class with Handler and Controller
#       - based on socketserver package
#    2. UDP Socket Client Class
############################################################################
# Developer: Heon-Hui Kim (2022. 04. 11)
############################################################################

import socket
import threading
import socketserver
import time
import abc

if __name__ == '__main__':
    import common_utils as utils
else:
    import base_socket.common_utils as utils

class ThreadedUdpRequestHandler(socketserver.BaseRequestHandler):
    __send_timer_handle = None
    __send_timer_interval = -1  # default value is 1 sec for interval of data sending timer
    __is_send_timer_alive = False

    def handle(self):
        # get controller_handle from server object
        controller = self.server.get_controller_handle()

        #data = self.request[0].strip()
        #sock = self.request[1].recv(1024)

        current_thread = threading.current_thread()

        #print()
        #print("=" * 100)
        #print(f'UDP Server (IP:{self.server.server_address[0]}, PORT:{self.server.server_address[1]})')
        #print("-" * 100)
        print(f'An UDP client(IP:{self.client_address[0]}, PORT:{self.client_address[1]}) is connected in {current_thread}')


        #self.request[1].setblocking(True)
        #self.request[1].settimeout(5)
        packet = self.request[0]
        print('received:', len(packet))

        #combiner = "".join(fragments)
        #print('combined:', fragments)

        '''
        try:
            data, client_ip = self.request[1].recvfrom(60000)
            print(client_ip, data)
            #time.sleep(1)
        #except OSError as e: #OSError or ConnectionResetError:
        except IOError as e: # socket.timeout:
            #print(e)
            flag = False
            #break
        '''

        #print(self.request[1])
        #data, client_ip = self.request[1].recvfrom(1024)
        #print(client_ip, data)
        #print(len)
        #print(len(self.request[0]))
        #packet = self.__receive_packet_from(self.request[1])
        #print(packet)
        '''
        while True:
            # wait for receiving data from client
            try:
                sock = self.request[1]

                #client_addr = self.client_address[0]
                packet = self.__receive_packet_from(sock)
                print(packet)
                if packet:

                    # parsing data
                    decoded_data = self.__decode_packet_to_data(packet)
                    # overiding function for implementing action procedure after receiving message from a client
                    ip = self.client_address[0]
                    port = self.client_address[1]
                    self.data_received_task(decoded_data, ip, port)
                else:
                    #self.stop_send_timer()
                    break
            except OSError or ConnectionResetError:
                #self.stop_send_timer()
                break
        '''
        print(f'The UDP client(IP:{self.client_address[0]}, PORT:{self.client_address[1]}) is disconnected')
        print("-" * 100)

    def send_data_to(self, msg, ip, port):
        self.__send_packet_to(self.__encode_data_to_packet(msg), ip, port)

    def start_send_timer(self, time_interval):
        self.__is_send_timer_alive = True
        self.__send_timer_interval = time_interval
        self.__send_data_timer_fun()

    def stop_send_timer(self):
        self.__is_send_timer_alive = False
        if self.__send_timer_handle is not None:
            self.__send_timer_handle.cancel()
            self.__send_timer_handle.join()

    def __send_data_timer_fun(self):
        if self.__is_send_timer_alive:

            # overiding function for implementing sending procedure for every sampling time
            self.periodic_data_sending_task()

            # and reset timer event handler
            self.__send_timer_handle = threading.Timer(self.__send_timer_interval, self.__send_data_timer_fun)
            self.__send_timer_handle.daemon = True
            self.__send_timer_handle.start()

    def __encode_data_to_packet(self, obj):
        return utils.encode(obj)

    def __decode_packet_to_data(self, obj):
        return utils.decode(obj)

    def __receive_packet_from(self, sock):
        return utils.recv_msg(sock)

    def __send_packet_to(self, sock, packet, ip, port):
        utils.send_udp_msg(sock, packet, ip, port)
        #utils.send_msg(sock, packet)

    @abc.abstractmethod
    def data_sending_task(self):
        pass

    @abc.abstractmethod
    def periodic_data_sending_task(self):
        pass

    @abc.abstractmethod
    def data_received_task(self, data, ip, port):
        pass

class ThreadedUdpServer(socketserver.ThreadingMixIn, socketserver.UDPServer):

    def __init__(self, server_address, request_handler_class, controller_handle=None):
        super().__init__(server_address, request_handler_class)
        self.__controller_handle = controller_handle

    def start(self):
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def get_controller_handle(self):
        return self.__controller_handle



class UdpClient(object):
    def __init__(self, ip_address, port_no):
        self.__is_receive_thread_alive = False
        self.__receive_thread_handle = None
        self.__socket = None
        self.__send_timer_handle = None
        self.__send_timer_interval = 1.0  # default value is 1 sec for interval of data sending timer
        self.__is_send_timer_alive = False
        self.__server_ip = (ip_address, port_no)
        self.__connect(ip_address, port_no)

    def get_server_ip(self):
        #print(self.__server_ip)
        return self.__server_ip

    def get_socket(self):
        return self.__socket

    def start_send_timer(self, time_interval):
        self.__is_send_timer_alive = True
        self.__send_timer_interval = time_interval
        self.__send_data_timer_fun()

    def start_received_thread(self):
        self.__is_receive_thread_alive = True
        # set receive timeout
        self.__socket.settimeout(3.0)
        self.__receive_thread_handle = threading.Thread(target=self.__receive_thread_fun)
        self.__receive_thread_handle.daemon = True
        self.__is_receive_thread_alive = True
        self.__receive_thread_handle.start()

    def send_data_to_server(self, data, ip, port):
        self.__send_packet_to(self.get_socket(), self.__encode_data_to_packet(data), ip, port)
        '''
        packet = self.__encode_data_to_packet(data)
        max_byte = 500
        loop_cnt = len(packet) // max_byte
        remains = len(packet) % max_byte
        for k in range(loop_cnt+1):
            start = k * max_byte
            end = start + max_byte
            if k <= loop_cnt:
                subdata = packet[start:end]
            else:
                subdata = packet[start:]
            #print(start, end, subdata)
            #self.__send_packet_to(self.get_socket(), subdata, ip, port)
            self.get_socket().sendto(subdata, (ip, port))
            #self.get_socket().sendall(subdata)
        '''



    def close(self):
        self.__is_send_timer_alive = False
        self.__is_receive_thread_alive = False

        #print('join start')
        if self.__send_timer_handle is not None:
            self.__send_timer_handle.join()
        if self.__receive_thread_handle is not None:
            self.__receive_thread_handle.join()

        #print('join end')
        self.__send_timer_handle = None
        self.__receive_thread_handle = None

        #print('start closing socket')
        self.__socket.close()
        self.__socket = None
        #print("Close socket")

    def __connect(self, ip, port):
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.__socket.connect((ip, port))
            #self.__socket.sendto(bytes('connect', 'utf-8'), (ip, port))

            print(f"Successfully connect to UDP Server (ip:{ip}, port:{port})")
        except IOError as e:
            print(f"Cannot connect to UDP Server (ip:{ip}, port:{port})")

    def __send_data_timer_fun(self):
        if self.__is_send_timer_alive:
            # the below function is called for every time interval
            self.data_sending_task()
            # and reset timer event handler
            self.__send_timer_handle = threading.Timer(self.__send_timer_interval, self.__send_data_timer_fun)
            self.__send_timer_handle.daemon = True
            self.__send_timer_handle.start()


    def __receive_thread_fun(self):
        while self.__is_receive_thread_alive:
            try:
                packet = self.__receive_packet_from_server()
                if packet:
                    decoded_data = self.__decode_packet_to_data(packet)
                    self.data_received_task(decoded_data)
            except IOError as e:
                #print(f'error={e}')
                pass

    def __encode_data_to_packet(self, obj):
        return utils.encode(obj)

    def __decode_packet_to_data(self, obj):
        return utils.decode(obj)

    def __receive_packet_from_server(self):
        return utils.recv_msg(self.__socket)

    def __send_packet_to(self, sock, packet, ip, port):
        utils.send_udp_msg(sock, packet, ip, port)



    #def __send_packet_to_server(self, packet):
    #    utils.send_msg(self.__socket, packet)

    @abc.abstractmethod
    def data_received_task(self, data):
        pass

    @abc.abstractmethod
    def data_sending_task(self):
        pass

if __name__ == '__main__':

    class MyUdpHandler(ThreadedUdpRequestHandler):
        count = 0
        def data_received_task(self, data, ip, port):
            data = {"data_0": self.count, "data_1": self.count}
            self.send_data_to(self.request, data)
            print(f'received from {ip}, {port} : {data}')
            '''
            if type(data) == dict:
                if data['cmd'] == 'once':
                    self.data_sending_task()
                elif data['cmd'] == 'start':
                    time_interval = data['interval']
                    self.start_send_timer(time_interval)
                elif data['cmd'] == 'stop':
                    self.stop_send_timer()
            elif type(data) == str:
                print(data)
            '''
        def data_sending_task(self):
            # get controller handle to access server's working data
            controller_handle = self.server.get_controller_handle()
            # set messages
            data = {"data_0": self.count, "data_1": self.count}
            self.send_data_to(self.request, data)
            print(f'[server] send to client: {data}')
            self.count += 1

        def periodic_data_sending_task(self):
            # get controller handle to access server's working data
            controller_handle = self.server.get_controller_handle()
            # set messages
            data = {"data_0": self.count, "data_1": self.count}
            self.send_data_to(self.request, data)
            print(f'[server] send to client: {data}')
            self.count -= 1



    # Example for implementing client class
    class MyUdpClient(UdpClient):
        def request_periodic_data_sending(self, interval):
            pass
            #data = {"cmd": 'start', 'interval': interval}
            #self.send_data_to_server(data)
            #print(f'[client] sending to server: {data}')


        def data_sending_task(self):
            data = {"cmd": 'once', "body": bytearray(5000)}
            ip =  self.get_server_ip()
            #self.send_data_to_server(data, ip[0], ip[1])
            #self.get_socket().sendto(data, ip)
            data = '0123456789' * 800
            self.send_data_to_server(data, ip[0], ip[1])

            print(f'[client] sending to server: {data}')

        def data_received_task(self, data):
            print(f'[client] receiving from server: {data}')

    port = 19998
    host_ip = socket.gethostbyname(socket.gethostname())

    #server_handler = MyTcpHandler()
    #server = ThreadedTcpServer((host_ip, port), MyTcpHandler, 'controller')
    server = ThreadedUdpServer((host_ip, port), MyUdpHandler)
    server.start()

    print(f'UDP Server (ip:{host_ip}, port:{port}) is running in thread: ')

    ip, port = server.server_address
    #server_thread = threading.Thread(target=server.serve_forever)
    #server_thread.daemon = True
    #server_thread.start()

    #client = TcpClient()
    #client.connect(host_ip, port)
    client = MyUdpClient(ip, port)
    client.start_send_timer(2.0)
    #client.request_periodic_data_sending_task(1)
    client.start_received_thread()


    time.sleep(5)
    client.close()

    time.sleep(2)
    server.shutdown()
    print('close server')


