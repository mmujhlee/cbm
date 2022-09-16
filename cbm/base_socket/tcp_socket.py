############################################################################
# Python Module for TCP Socket Programming
############################################################################
# Main Features:
#    1. Multi-Threaded TCP Socket Server Class with Handler and Controller
#       - based on socketserver package
#    2. TCP Socket Client Class
############################################################################
# Developer: Heon-Hui Kim (2022. 03. 31)
# revision history
# 2022. 04. 11 : make package to be [4byte_len(encoded_message) + encoded_message]
#                capsualation of [len(encode(msg)) + encode(msg)]
############################################################################

import socket
import threading
import socketserver
import time
import abc

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import common_utils as utils

class ThreadedTcpRequestHandler(socketserver.BaseRequestHandler):
    __send_timer_handle = None
    __send_timer_interval = -1  # default value is 1 sec for interval of data sending timer
    __is_send_timer_alive = False

    def handle(self):
        # get controller_handle from server object
        controller = self.server.get_controller_handle()

        sock = self.request
        current_thread = threading.current_thread()

        print()
        print("=" * 100)
        print(f'TCP Server (IP:{self.server.server_address[0]}, PORT:{self.server.server_address[1]})')
        print("-" * 100)
        print(f'A client(IP:{self.client_address[0]}, PORT:{self.client_address[1]}) is connected in {current_thread}')

        while True:
            # wait for receiving data from client
            try:
                packet = self.__receive_packet_from(sock)
                if packet:
                    # parsing data
                    decoded_data = self.__decode_packet_to_data(packet)
                    # overiding function for implementing action procedure after receiving message from a client
                    self.data_received_task(decoded_data)
                else:
                    self.stop_send_timer()
                    break
            except OSError or ConnectionResetError:
                self.stop_send_timer()
                break
        print(f'The client(IP:{self.client_address[0]}, PORT:{self.client_address[1]}) is disconnected')
        print("-" * 100)

    def send_data_to(self, sock, msg):
        self.__send_packet_to(sock, self.__encode_data_to_packet(msg))

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

    def __send_packet_to(self, sock, packet):
        utils.send_msg(sock, packet)

    @abc.abstractmethod
    def data_sending_task(self):
        pass

    @abc.abstractmethod
    def periodic_data_sending_task(self):
        pass

    @abc.abstractmethod
    def data_received_task(self, data):
        pass

class ThreadedTcpServer(socketserver.ThreadingMixIn, socketserver.TCPServer):

    def __init__(self, server_address, request_handler_class, controller_handle=None):
        super().__init__(server_address, request_handler_class)
        self.__controller_handle = controller_handle

    def start(self):
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def get_controller_handle(self):
        return self.__controller_handle



class TcpClient(object):
    def __init__(self, ip_address, port_no):
        self.__is_receive_thread_alive = False
        self.__receive_thread_handle = None
        self.__socket = None
        self.__send_timer_handle = None
        self.__send_timer_interval = 1.0  # default value is 1 sec for interval of data sending timer
        self.__is_send_timer_alive = False
        self.__ip_address = ip_address
        self.__port_no = port_no
        #self.connect(ip_address, port_no)

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

    def send_data_to_server(self, data):
        self.__send_packet_to_server(self.__encode_data_to_packet(data))

    def connect(self):
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__socket.connect((self.__ip_address, self.__port_no))

            print(f"Successfully connect to TCP Server (ip:{self.__ip_address}, port:{self.__port_no})")
        except IOError as e:
            print(f"Cannot connect to TCP Server (ip:{self.__ip_address}, port:{self.__port_no})")

    def disconnect(self):
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
                    #print(data)
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

    def __send_packet_to_server(self, packet):
        utils.send_msg(self.__socket, packet)

    @abc.abstractmethod
    def data_received_task(self, data):
        pass

    @abc.abstractmethod
    def data_sending_task(self):
        pass

if __name__ == '__main__':
    '''
    # This is an example of how to use this module 
    class MyTcpHandler(ThreadedTcpRequestHandler):
        def data_received_task(self, data):
            pass
        def data_sending_task(self):
            pass
        def periodic_data_sending_task(self):
            pass
    
    # Example for implementing client class
    class MyTcpClient(TcpClient):
        def data_sending_task(self):
            pass
        def data_received_task(self, data):
            pass
            
    # more detailed implementation examples are as below: 
    '''

    class MyTcpHandler(ThreadedTcpRequestHandler):
        count = 0

        def data_received_task(self, data):
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
    class MyTcpClient(TcpClient):
        def request_periodic_data_sending(self, interval):
            data = {"cmd": 'start', 'interval': interval}
            self.send_data_to_server(data)
            print(f'[client] sending to server: {data}')

        def data_sending_task(self):
            #data = {"cmd": 'once', "body": {"msg": "This is a test."}}
            data = 'this is a message'
            self.send_data_to_server(data)
            print(f'[client] sending to server: {data}')

        def data_received_task(self, data):
            print(f'[client] receiving from server: {data}')

    port = 9999
    host_ip = socket.gethostbyname(socket.gethostname())

    #server_handler = MyTcpHandler()
    #server = ThreadedTcpServer((host_ip, port), MyTcpHandler, 'controller')
    server = ThreadedTcpServer((host_ip, port), MyTcpHandler)
    server.start()

    print(f'TCP Server (ip:{host_ip}, port:{port}) is running in thread: ')

    ip, port = server.server_address
    #server_thread = threading.Thread(target=server.serve_forever)
    #server_thread.daemon = True
    #server_thread.start()

    #client = TcpClient()
    #client.connect(host_ip, port)
    client = MyTcpClient(ip, port)
    client.connect()

    # client.start_send_timer(1.0)
    client.request_periodic_data_sending(1)
    client.start_received_thread()


    time.sleep(5)
    client.close()
    time.sleep(2)
    server.shutdown()
    print('close server')


