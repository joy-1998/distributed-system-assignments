# Import Statements needed for content provider to function
import xmlrpc.client
import time

class ContentProviders:
   def __init__(self, available_servers, lock_server_url):
       self.server_list = available_servers
       self.lock_server_url = lock_server_url

   def send_files(self, filename):  # to send the files to the specified servers
       try:
           with open(filename, "rb") as file:
               file_content = xmlrpc.client.Binary(file.read())  # to read the files that are available
           lock_server_proxy = xmlrpc.client.ServerProxy(self.lock_server_url)
           while not lock_server_proxy.acquire_lock():
               print("Waiting for lock...")
               time.sleep(1)
           for server in self.server_list:
               server_proxy = xmlrpc.client.ServerProxy(server)
               result = server_proxy.save_files(filename, file_content)
               if result == "Success":
                   print(f"File '{filename}' transmitted to server at {server}")
               else:
                   print(f"Error occurred while sending the required file '{filename}' to the server {server}: {result}")
           lock_server_proxy.release_lock()
       except Exception as e:
           print(f"Error occurred while sending the file '{filename}': {str(e)}")


   def content_provider(self, filename):
       while True:  # Loop executes until interrupted by the user
           self.send_files(filename)
           time.sleep(120)  # Wait for 120 seconds before re-sending the files - this is done for replication at all times

if __name__ == "__main__":
    server_list = ["http://localhost:8080"]
    lock_server_url = "http://localhost:8081"
    content_provider = ContentProviders(server_list, lock_server_url)
    content_provider.content_provider('file1.txt')