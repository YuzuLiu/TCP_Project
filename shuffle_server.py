from socket import *
import requests

class MySocket:

    def __init__(self,host="localhost",port=3000):

        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((host, port))

    def send_shuffle(self):
        self.sock.send('Shuffle list'.encode('utf-8'))
		
s = MySocket()
s.send_shuffle()