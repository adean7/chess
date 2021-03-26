import pickle
import socket

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "192.168.0.11"
        self.port = 5555
        self.addr = (self.server, self.port)
        self.player = self.connect()

        self.connected = True if self.player is not None else False

    def get_player(self):
        return self.player

    def connect(self):
        try:
            self.client.connect(self.addr)
            #return self.client.recv(2048).decode()
            return pickle.loads(self.client.recv(4096))
        except:
            return None

    def send(self, data):
        try:
            #self.client.send(str.encode(data))
            self.client.send(pickle.dumps(data))

            '''
            new_data = []
            while True:
                print(222)
                packet = self.client.recv(4096)
                if not packet: break
                new_data.append(packet)

            new_data_arr = pickle.loads(b"".join(data))

            return new_data_arr
            '''

            return pickle.loads(self.client.recv(16384))

        except socket.error as e:
            print(e)

