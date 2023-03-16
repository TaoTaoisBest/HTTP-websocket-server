import socket
from _thread import *
import threading
import mimetypes
import os
import re
import signal
import sys

t_lock = threading.Lock()

def shutdown_server(signal, frame):
   print("Server shutdown command recieved (ctrl+C), shutting down/closing server...")
   server_socket.close()
   sys.exit(1)

def threaded(client_socket):
    while True:
        try:
            msg = client_socket.recv(2048).decode('utf-8')
            client_socket.settimeout(5)
            print(msg)
            msg_sections = re.split(' |\n', msg)
            get_or_post = msg_sections[0]
            command = msg_sections[1]
            if get_or_post == 'GET':
                if command == '/':
                    header = 'HTTP/1.1 200 OK\nContent-Type: text/html\n\n'
                    try:
                        file = open('index.html', 'r')
                        html_data = file.read()
                        file.close()
                    except:
                        html_data = '<html><body><h>error!</h></body></html>'
                    client_socket.send((header + html_data).encode('utf-8'))
                    # print((header + html_data))
                elif msg_sections[9] == 'Range:':
                    # for html video/audio tag streaming on safari
                    # ref : https://xbddc.github.io/2019/05/10/video-tag-in-safari/
                    file_name = command.split('/')[1]
                    content_type = mimetypes.guess_type(file_name)[0]

                    buf = msg_sections[10]
                    data_range = buf.split('=')[1]
                    start = int(data_range.split('-')[0])
                    end = int(data_range.split('-')[1])

                    file_stats = os.stat(file_name)
                    file_size = file_stats.st_size

                    header = f'HTTP/1.1 206 Partial Content\n'\
                             f'Accept-Ranges: bytes\n' \
                             f'Content-Range: bytes {str(start)}-{str(end)}/{str(file_size)}\n' \
                             f'Content-Length: {str(end-start+1)}\n' \
                             f'Content-Type: {content_type}\n\n'
                    try:
                        file = open(file_name, 'rb')
                        _ = file.read(start)
                        video_data = file.read(end-start+1)
                        file.close()
                        response = b''.join([header.encode('utf-8'), video_data])
                        client_socket.send(response)
                        print(header)
                    except:
                        video_data = ''
                        client_socket.send((header + video_data).encode('utf-8'))
                        print("video/audio error!")
                else :
                    file_name = command.split('/')[1]
                    content_type = mimetypes.guess_type(file_name)[0]
                    header = f'HTTP/1.1 200 OK\nContent-Type: {content_type}\n\n'
                    try:
                        file = open(file_name, 'rb')
                        video_data = file.read()
                        file.close()
                        response = b''.join([header.encode('utf-8'), video_data])
                        client_socket.send(response)
                    except:
                        video_data = ''
                        client_socket.send((header + video_data).encode('utf-8'))
                        print("file error!")
            else:
                header = 'HTTP/1.1 200 OK\nContent-Type: text/html\n\n'
                data = '<html><body><h1>Success</h1></body></html>'
                client_socket.send((header + data).encode('utf-8'))
        except:
            client_socket.close()
            print('out!')
            break


if __name__ == '__main__':
    signal.signal(signal.SIGINT, shutdown_server)
    host = ''
    port = 8000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    message = ''
    while True:
        client_socket, addr = server_socket.accept()
        print(addr[0], ' ; ', addr[1])
        start_new_thread(threaded, (client_socket,))

# GET /video.mp4 HTTP/1.1
# Accept: */*
# Connection: Keep-Alive
# Range: bytes=0-1
# Host: localhost:8000
# Accept-Language: zh-TW,zh-Hant;q=0.9
# User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15
# Referer: http://localhost:8000/
# Accept-Encoding: identity
# X-Playback-Session-Id: AAAE8170-F003-489A-8D5E-394CC4110B33

# HTTP/1.1 200 OK
# Content-Range: bytes=0-1/2865887
# Content-Type: video/mp4
# Content-Length: 2



