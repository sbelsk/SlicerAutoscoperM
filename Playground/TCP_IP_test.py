### CONNECTION 
import socket
client  = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
HOST = 'localhost'
PORT = 30007
client.connect((HOST, PORT))
# while 1:
    # data = conn.recv(1024)
    # if not data: break
    # conn.sendall(data)
# conn.close()
BUFFER_SIZE = 1024
client.sendall(b'Hello, world')


## if loadTrial is functional Python- we cal loadTrial(client, 1)




## is the goal to create  loadTrial (matlab function analog) to handle the communication that autoscoper
# handleMessage() is expecting...
function loadTrial(autoscoper_socket, trial_file)
%LOAD_TRIAL Summary of this function goes here
%   Detailed explanation goes here
%Load trial
fwrite(autoscoper_socket,[1 trial_file]);
while autoscoper_socket.BytesAvailable == 0
    pause(1)
end
data = fread(autoscoper_socket, autoscoper_socket.BytesAvailable);
end