import threading
import time
import xmlrpc.client
import xmlrpc.server

class ContentProvider:
    def __init__(self, file_srv_url, port, peers):
        self.server_proxy = xmlrpc.client.ServerProxy(file_srv_url)
        self.port = port
        self.peers = peers
        self.lock_acquired = False
        self.replies_received = 0
        self.lock = threading.Lock()

        # Create an XML-RPC server
        self.server = xmlrpc.server.SimpleXMLRPCServer(('localhost', self.port), allow_none=True)
        self.server.register_introspection_functions()
        self.server.register_instance(self)

        # Start the server in a separate thread
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True  # Set the thread as daemon to stop with the main thread
        self.server_thread.start()

    def send_file(self, filename):
        print(f"Attempting to send file '{filename}'...")
        try:
            with open(filename, "rb") as file:
                file_content = xmlrpc.client.Binary(file.read())
                result = self.server_proxy.save_files(filename, file_content)
                if result == "Success":
                    print(f"File '{filename}' sent successfully.")
                else:
                    print(f"Error occurred while sending the required file '{filename}' to the server: {result}")
        except Exception as e:
            print(f"Error occurred while sending the required file '{filename}': {e}")

    def send_lock_request(self, filename):
        print(f"Sending lock request for file '{filename}'...")
        for peer in self.peers:
            try:
                with xmlrpc.client.ServerProxy(f"http://{peer[0]}:{peer[1]}/") as proxy:
                    proxy.handle_lock_request(filename)
            except Exception as e:
                print(f"Failed to connect to {peer}. Retrying in 5 seconds...")
                print(e)
                time.sleep(5)

    def send_lock_reply(self, filename):
        print(f"Sending lock reply for file '{filename}'...")
        for peer in self.peers:
            try:
                with xmlrpc.client.ServerProxy(f"http://{peer[0]}:{peer[1]}/") as proxy:
                    proxy.handle_lock_reply(filename)
            except Exception as e:
                print(f"Failed to connect to {peer}. Retrying in 5 seconds...")
                time.sleep(5)

    def handle_lock_request(self, filename):
        try:
            print(f"Received lock request for file '{filename}'.")
            with self.lock:
                self.send_lock_reply(filename)
                self.replies_received += 1
                if self.replies_received == len(self.peers):
                    self.lock_acquired = True
                    print(f"Lock acquired for file '{filename}'.")
                else:
                    print("Here2")
        except Exception as e:
            print(f"Error in handle_lock_request: {e}")

    def handle_lock_reply(self, filename):
        print(f"Received lock reply for file '{filename}'.")
        with self.lock:
            if self.initiated_lock_request:  # Check if this instance requested the lock
                self.replies_received += 1
                if self.replies_received == len(self.peers):
                    self.lock_acquired = False
                    self.initiated_lock_request = False  # Reset flag
                    print(f"Lock released for file '{filename}'.")
                else:
                    print("Here")
            else:
                print(f"Ignoring lock reply for file '{filename}' as lock wasn't requested by this instance.")

    def retrigger(self, filename):
        self.send_lock_request(filename)

    def acquire_lock_thread(self, filename):
        while True:
            if not self.lock_acquired:
                self.send_lock_request(filename)
                while not self.lock_acquired:
                    time.sleep(1) # Simulate waiting for replies
                self.send_file(filename)
                print(f"Lock released for file '{filename}'.")
                with self.lock:
                    self.lock_acquired = False
                    self.replies_received = 0
                print(f"Waiting for 10 seconds before restarting the transfer process for file '{filename}'...")
                time.sleep(10) # Wait for 10 seconds before restarting
            else:
                time.sleep(1)

if __name__ == "__main__":
    server_url = "http://localhost:8080"
    content_provider = ContentProvider(server_url, 8083, [('localhost', 8082), ('localhost', 8081)])
    lock_thread = threading.Thread(target=content_provider.acquire_lock_thread, args=("file3.txt",))
    lock_thread.daemon = True  # Set the thread as daemon to stop with the main thread
    lock_thread.start()

    try:
        while True:
            time.sleep(1) # Keep the main thread alive
    except KeyboardInterrupt:
        print("Terminating...")
