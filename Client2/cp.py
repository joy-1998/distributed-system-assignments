# Import Statements needed for content provider to function
import xmlrpc.client
import time

class ContentProviders:
   def __init__(self, available_servers):
       self.server_list = available_servers


   def send_files(self, filename):  # to send the files to the specified servers
       try:
           with open(filename, "rb") as file:
               file_content = xmlrpc.client.Binary(file.read())  # to read the files that are available
           for server in self.server_list:
               server_proxy = xmlrpc.client.ServerProxy(server) #http://localhost:8080
               result = server_proxy.save_files(filename, file_content)
               if result == "Success":
                   print(f"File '{filename}' transmitted to server at {server}")
               else:
                   print(
                       f"Error occurred while sending the required file '{filename}' to the server {server}: {result}")
       except FileNotFoundError:  # Error Handlers
           print(f"File '{filename}' not available, please try again.")
       except Exception as e:  # Error Handlers
           print(f"Error occurred while sending the file '{filename}': {str(e)}")


   def content_provider(self, filename):
       while True:  # Loop executes until interrupted by the user
           self.send_files(filename)
           time.sleep(120)  # Wait for 120 seconds before re-sending the files - this is done for replication at all times

if __name__ == "__main__":
   # List of available servers
   server_list = ["http://localhost:8080"]
   content_provider = ContentProviders(server_list)  # content provider calls
   content_provider.content_provider('file1.txt')  # target files that needs to be sent to all the servers specified.
