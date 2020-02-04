from socket import *
from threading import Thread
from os.path import getsize
import os
import random

HOST = 'localhost'
PORT = 3000
s = socket(AF_INET, SOCK_STREAM)
s.bind((HOST, PORT))
# set to non-blocking
s.setblocking(0)
s.listen(5)
print('{} server open at port {}...'.format(HOST, PORT))

def bytes_to_number(self, b):
    res = 0
    for i in range(4):
        res += b[i] << (i*8)
    return res

upload_files = []
#######################################
try:
    f = open('username.txt', 'x')
    f.close()
except:
    pass

while True:
    # use try except to avoid errors
    try:
        client, addr = s.accept()
        print('Client Address：{},Port ：{}'.format(addr[0], addr[1]))
        # set client socket to non-blocking
        client.setblocking(0)

        # to see the request message from client
        request_data = client.recv(1024).decode('utf-8')

        print(request_data)
        
        action = request_data.split()[0]
        request = ' '.join(request_data.split()[1:])

        print(action)
        print(request)

        if action == 'username':
            check_username = request
            same = 0

            current_directory = os.path.dirname(os.path.abspath(__file__))
            f = open(os.path.join(current_directory, 'username.txt'), 'r+')

            usernames = f.readline()
            while usernames:
                print('Checking Usernames... ' + usernames.rstrip() + ' with ' + check_username)
                if check_username == usernames.rstrip():
                    same = 1
                    print('Breaking...')
                    break
                else:
                    same = 0
                    usernames = f.readline()

            if same == 0:
                f.write(check_username + "\n")
                f.close()
                client.send('Yes'.encode('utf-8'))
            elif same == 1:
                f.close()
                client.send('No'.encode('utf-8'))

        if action == 'Uploading':
            client.setblocking(1)
            musicFileName = request.rsplit('\\', 1)[-1]
            f = open(musicFileName, 'wb')
            print('Filename: ' + musicFileName)
            while True:
                client.sendall('getfile'.encode('utf-8'))
                print('Waiting for filesize...')
                size = client.recv(4)
                
                res = 0
                for i in range(4):
                    res += size[i] << (i*8)
                size = res

                print('Total size: ' + str(size))
                current_size = 0
                buffer = b""
                while current_size < size:
                    data = client.recv(1024)
                    if not data:
                        print('Breaking...')
                        break
                    if len(data) + current_size > size:
                        data = data[:size-current_size]
                    buffer += data
                    current_size += len(data)
                    f.write(data)

                print(len(upload_files))
                client.sendall(str(len(upload_files)).encode('utf-8'))#
                print('Sending upload number', len(upload_files))
                upload_files.append(musicFileName)#
                print(upload_files)
                break
            print('File Received')
            f.close()
        
        if action == 'Downloading':
            client.setblocking(1)
            length = os.path.getsize(request)

            result = bytearray()
            result.append(length & 255)
            for i in range(3):
                length = length >> 8
                result.append(length & 255)

            client.sendall(result)
            with open(request, 'rb') as f:
                data = f.read(1024)
                while data:
                    client.sendall(data)
                    data = f.read(1024)
            print("Finishing Downloading..." + request)
            

        if action == 'Exchange':
            if len(upload_files) != 0:
                filename = upload_files[int(request)]
                print('Wants to exchange ', filename)
                client.sendall(filename.encode('utf-8'))
                print('Send ' + upload_files[int(request)])
            if len(upload_files) == 0:
                client.sendall('No'.encode('utf-8'))
                print('Sending no upload files.')

        if action == 'Shuffle':
            finish = 1
            randomized_list = upload_files[:]
            while finish >= 0:
                random.shuffle(randomized_list)
                print('Randomized List: ', randomized_list)
                for a, b in zip(upload_files, randomized_list):
                    if a == b:
                        continue
                        print('Continue randomize...')
                    else:
                        finish = -1      
            print('Finished...')
            upload_files = randomized_list
            print(upload_files)

        if int(action) <= 5 and int(action) >= 1:
            with open('rating_music.txt', 'a') as f:
                f.write(request + ' ' + action + '\n')
                f.close()
        
        if int(action) == 100:
            client.setblocking(1)
            if getsize('rating_music.txt') == 0:
                client.sendall('No'.encode('utf-8'))
            else:
                file = open('rating_music.txt').readlines()
                scores_tuples = []
                rating_data = ''

                for line in file:
                    name, score = line.split()[0], float(line.split()[1])
                    scores_tuples.append((name,score))
                scores_tuples.sort(key=lambda t: t[1], reverse=True)
                print("HIGHSCORES\n")
                for i, (name, score) in enumerate(scores_tuples[:10]):
                    print("{}. Rate: {} - Music: {}".format(i+1, score, name))

                    rating_data += "{}. Rate: {} - Music: {}\n".format(i+1, score, name)
                client.sendall(rating_data.encode('utf-8'))
                f.close()
    except:
        pass  # pass if error

