import socket
import threading
import time
import uuid
from google.protobuf import message
import project2021_ece441_pb2

# Group ID Assigned by Professor
GROUP = 22

# Server Socket
IP = '194.177.207.90'
PORT = 65432 
HOST = (IP, PORT)

def get_mac():
  return ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])



# Initialize a TCP Connection with Server
def tcp_init(host):
  client_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client_fd.connect(host)
  return client_fd


# Close Client Socket 
def tcp_fin(client_fd):
  client_fd.close()


# Helper Function to Set Header Information on a Message 
def header_set(message_header, group, type):
  message_header.id = group
  message_header.type = project2021_ece441_pb2.ece441_type.Value(type)
  return None


# Helper Function to Set Student Information on a Message 
def students_set(message_type): 
  student = message_type.student.add()
  student.aem = socket.htonl(2824)
  student.name = 'Stoltidis Alexandros'
  student.email = 'stalexandros@uth.gr'

  student = message_type.student.add()
  student.aem = socket.htonl(2789)
  student.name = 'Lantzos Stergios'
  student.email = 'lstergios@uth.gr'
  
  return None


# Serialize Message, Send Byte Stream and Get Response
def send_receive(message, client_fd, socket_lock):
  # Convert Object to Byte-String
  request = message.SerializeToString()


  # Start of Critical Section
  if socket_lock:
    socket_lock.acquire()
  
  # Send Request as a Byte-String
  client_fd.sendall(request)

  # Get Response as a Byte-String
  response = client_fd.recv(1024)
  
  # End of Critical Section
  if socket_lock:
    socket_lock.release()

  if not response:
    return False

  # Convert Byte-String to Object
  message.ParseFromString(response)

  return True


# Handle Connection Establishment with "conn_req" and "conn_resp" 
def conn_req_res(client_fd, group):
  message = project2021_ece441_pb2.project_message()
  
  # Header
  header_set(message.conn_req_msg.header, group, 'ECE441_CONN_REQ')

  # Data (Group Members)
  students_set(message.conn_req_msg)

  # Send Message and Receive Response
  send_receive(message, client_fd, None)
  
  # Check for Successful Response
  if message.WhichOneof('msg') != 'conn_resp_msg':
    return -1

  if message.conn_resp_msg.direction != project2021_ece441_pb2.ece441_direction.Value('SUCCESSFUL'):
    return -1

  # print(message)

  return message.conn_resp_msg.interval


# Handle Periodic HELLO Messages
def hello_echo(client_fd, socket_lock, group, interval):
  message = project2021_ece441_pb2.project_message()
  
  while not exit.is_set():

    # Header
    header_set(message.hello_msg.header, group, 'ECE441_HELLO')
    
    # Send Message and Receive Response
    if not send_receive(message, client_fd, socket_lock):
      return False

    # Check for Successful Response
    if message.WhichOneof('msg') != 'hello_msg':
      return -1

    # print(message)

    exit.wait(interval)

  return 0


# Handle Netstat Request "netstat_req" and "netstat_resp"
def netstat_req_res(client_fd, group):
  message = project2021_ece441_pb2.project_message()
  
  # Header
  header_set(message.netstat_req_msg.header, group, 'ECE441_NETSTAT_REQ')
  
  # Data (Group Members)
  students_set(message.netstat_req_msg)
  
  # Send Message and Receive Response
  if not send_receive(message, client_fd, socket_lock):
    return False

  # Check for Successful Response
  if message.WhichOneof('msg') != 'netstat_resp_msg':
    return False

  if message.netstat_resp_msg.direction != project2021_ece441_pb2.ece441_direction.Value('SUCCESSFUL'):
    return False

  # print(message)

  return True


# Handle Data Transmission when Netstat Handshake is Successful 
def netstat_data(client_fd, group):
  message = project2021_ece441_pb2.project_message()

  # Header
  header_set(message.netstat_data_msg.header, group, 'ECE441_NETSTAT_DATA')
  
  # Direction Set
  message.netstat_data_msg.direction = project2021_ece441_pb2.ece441_direction.Value('SUCCESSFUL')
  
  # MAC Address 
  message.netstat_data_msg.mac_address = get_mac()

  # IP Address 
  message.netstat_data_msg.ip_address = socket.gethostbyname(socket.gethostname())
  
  # Send Message and Receive Response
  if not send_receive(message, client_fd, socket_lock):
    return False
  
  # Check for Successful Response
  if message.WhichOneof('msg') != 'netstat_data_ack_msg':
    return False

  if message.netstat_data_ack_msg.direction != project2021_ece441_pb2.ece441_direction.Value('SUCCESSFUL'):
    return False
  
  # print(message)
  return True


def netmeas_req_res(client_fd, group):
  message = project2021_ece441_pb2.project_message()
  
  # Header
  header_set(message.netmeas_req_msg.header, group, 'ECE441_NETMEAS_REQ')
  
  # Data (Group Members)
  students_set(message.netmeas_req_msg)
  
  # Send Message and Receive Response
  if not send_receive(message, client_fd, socket_lock):
    return False

  # Check for Successful Response
  if message.WhichOneof('msg') != 'netmeas_resp_msg':
    return False

  if message.netmeas_resp_msg.direction != project2021_ece441_pb2.ece441_direction.Value('SUCCESSFUL'):
    return False

  print(message)

  return True


def netmeas_data(client_fd, group):
  message = project2021_ece441_pb2.project_message()

  # Header
  header_set(message.netmeas_data_msg.header, group, 'ECE441_NETMEAS_REPORT')
  
  # Direction Set
  message.netmeas_data_msg.direction = project2021_ece441_pb2.ece441_direction.Value('SUCCESSFUL')

  # Report
  message.netmeas_data_msg.report = 0 

  # Send Message and Receive Response
  if not send_receive(message, client_fd, socket_lock):
    return False

  # Check for Successful Response
  if message.WhichOneof('msg') != 'netmeas_data_ack_msg':
    return False

  if message.netmeas_data_ack_msg.direction != project2021_ece441_pb2.ece441_direction.Value('SUCCESSFUL'):
    return False

  # print(message)


# Initialize TCP Connection with Remote Server
client_fd = tcp_init(HOST)
print('Connected to:', HOST)

# Get Server HELLO Message Interval
interval = conn_req_res(client_fd, GROUP)
print('HELLO Interval:', interval)

# Create Thread to Periodically Send HELLO Messages and a Lock to Synchronize Socket I/Os 
print('Spawining HELLO Thread...')

socket_lock = threading.Lock()
exit = threading.Event() #Functionality: Sleep and Return
thread = threading.Thread(target=hello_echo, args=[client_fd, socket_lock, GROUP, interval])


thread.start()

# Netstat Handshake
if netstat_req_res(client_fd, GROUP):
  if netstat_data(client_fd, GROUP):
    if netmeas_req_res(client_fd, GROUP):
      netmeas_data(client_fd, GROUP)






print('Terminating HELLO Thread...')
exit.set() # Exit Sleeping State and Return
thread.join()

# End TPC Connection
tcp_fin(client_fd)
print('Disconnected from:', HOST)

