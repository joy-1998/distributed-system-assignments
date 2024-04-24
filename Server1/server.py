# Import Statements needed for server to function
import socket
import threading
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

class RequestHandler(SimpleXMLRPCRequestHandler):
   rpc_paths = ('/RPC2',)  # XML Request Handler

class ServerFile:
   def __init__(self, server_id):
       self.server_id = server_id #(CURRENT_IP, PORT)
       self.files = {}
       self.nearby_list = []
       self.already_req_servers = []
       self.file_hashes = {}
       self.lock = threading.Lock()

   def get_files(self, filename):  # to fetch the required file
       current_server = 'http://' + self.server_id[0] + ':' + str(self.server_id[1])
       if filename in self.files:
           print(f"the file '{filename}' is found on the Server {self.server_id}.")
           return xmlrpc.client.Binary(self.files[filename])
       else:
           #  Request forwarder to the nearby servers
           print(f"File '{filename}' not found on Server {self.server_id}. Forwarding request...")
           for nearby in self.nearby_list:
               if nearby != current_server and nearby not in self.already_req_servers:
                   try:
                       socket.setdefaulttimeout(5)
                       nearby_proxy = xmlrpc.client.ServerProxy(nearby)
                       print("BeforeCall")
                       try:
                           file_content = nearby_proxy.get_files(filename)
                       except socket.timeout:
                           print("timeout")
                           self.already_req_servers.append(nearby)
                           return "File not available"
                       print("AfterCall")
                       if file_content != "File not available":
                           # sync with servers
                           print(f"File '{filename}' available on the server {nearby}. Updating current local copy...")
                           self.files[filename] = file_content.data
                           self.save_files(filename, file_content)
                           return file_content
                   except Exception as e:
                       print(f"Error while requesting file '{filename}' from Server {nearby}: {str(e)}")
                   self.already_req_servers(nearby)
           return "File not available"

   def save_files(self, filename, content):  # This function is used to save the incoming files from the Content Providers
       file_hash = hashlib.sha256(content.data).hexdigest()
       if file_hash not in self.file_hashes:
           self.files[filename] = content.data
           self.file_hashes[file_hash] = filename  # Store the hash to detect duplicates
           with open(filename, "wb") as file:
               file.write(content.data)
           print(f"File '{filename}' updated on Server {self.server_id}.")
           return "Success"
       else:
           print(f"Duplicate file '{filename}' detected. Not updating the server.")
           return "Duplicate file"

   def serve(self):  # Server instantiation
       server1 = SimpleXMLRPCServer(self.server_id, requestHandler=RequestHandler,
                                    allow_none=True)  # XML RPC server initiation
       server1.register_instance(self)
       print(f"Server on Node1 : {self.server_id} has been started")  # adding logger for running
       server1.serve_forever()  # To keep the server running until user interrupts


if __name__ == "__main__":
   PORT = 8080
   CURRENT_IP = "localhost"
   server = ServerFile((CURRENT_IP, PORT))  # sending the current server ip and desired port as a tuple
   server.nearby_list = ["http://localhost:8080"]  # list of servers with their private servers
   threading.Thread(target=server.serve).start()  # Threads that are started