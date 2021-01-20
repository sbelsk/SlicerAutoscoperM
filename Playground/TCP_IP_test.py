# ### CONNECTION (firs implementation using socket)
# import socket
# from struct import pack

# client  = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# print('socket instantiated')
# HOST = 'localhost'
# PORT = 30007
# client.connect((HOST, PORT))
# print('socket connected')

# conn_type = 1
# pp = b"C:\\Dev\\autoscoper-git\\build\\install\\bin\\Release\\sample_data\\wrist.cfg"
# data = pack('i 66s', conn_type, pp)
# client.sendall(data)


### CONNECTION: QTcpSocket
import qt
HOST = 'localhost'
PORT = 30007
client = qt.QTcpSocket()
client.connectToHost(HOST, PORT)
client.waitForConnected()


conn_type = b"1"
pp = b"C:\\Dev\\autoscoper-git\\build\\install\\bin\\Release\\sample_data\\wrist.cfg"
data = conn_type + pp
client.write(data)
client.flush()

