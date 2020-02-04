from socket import *
import requests

class MySocket:

    def __init__(self,host="localhost",port=3000):

        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((host, port))

    def send_username(self, username):
        self.sock.send('username {}'.format(username).encode('utf-8'))

    def get_data(self):
        return self.sock.recv(1024)