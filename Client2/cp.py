import socket
import threading
import time
import xmlrpc.client

class ContentProvider:
    def __init__(self, file_srv_url, port, peers):
        self.server_proxy = xmlrpc.client.ServerProxy(file_srv_url)
        self.port = port
        self.peers = peers # List of (host, port) tuples for other instances
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', self.port))
        self.server_socket.listen(len(self.peers))
        self.lock_acquired = False
        self.replies_received = 0

    def send_file(self, filename):
        print(f"Attempting to send file '{filename}'...")
        with open(filename, "rb") as file:
            file_content = xmlrpc.client.Binary(file.read())
            result = self.server_proxy.save_files(filename, file_content)
            if result == "Success":
                print(f"File '{filename}' sent successfully.")
            else:
                print(f"Error occurred while sending the required file '{filename}' to the server: {result}")
            time.sleep(10)
            print(f"values")
            self.retrigger(filename)

    def send_lock_request(self, filename):
        print(f"Sending lock request for file '{filename}'...")
        for peer in self.peers:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect(peer)
                client_socket.sendall(f"REQUEST:{filename}".encode())
                client_socket.close()
            except socket.error:
                print(f"Failed to connect to {peer}. Retrying in 5 seconds...")
                time.sleep(5)

    def send_lock_reply(self, filename):
        print(f"Sending lock reply for file '{filename}'...")
        for peer in self.peers:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect(peer)
                client_socket.sendall(f"REPLY:{filename}".encode())
                client_socket.close()
            except socket.error:
                print(f"Failed to connect to {peer}. Retrying in 5 seconds...")
                time.sleep(20)

    def handle_lock_request(self, connection, address):
        data = connection.recv(1024).decode()
        if data.startswith("REQUEST:"):
            filename = data.split(":")[1]
            print(f"Received lock request for file '{filename}' from {address}.")
            self.send_lock_reply(filename)
            self.replies_received += 1
            if self.replies_received == len(self.peers):
                self.lock_acquired = True
                print(f"Lock acquired for file '{filename}'.")
        elif data.startswith("REPLY:"):
            print(f"Received lock reply from {address}.")
            self.replies_received += 1
            if self.replies_received == len(self.peers):
                self.lock_acquired = False
                print(f"Lock released for file '{filename}'.")

    def acquire_lock_thread(self, filename):
        while True:
            if not self.lock_acquired:
                self.send_lock_request(filename)
                while not self.lock_acquired:
                    connection, address = self.server_socket.accept()
                    self.handle_lock_request(connection, address)
                    connection.close()
                self.send_file(filename)
                print(f"Lock released for file '{filename}'.")
                self.lock_acquired = False
                self.replies_received = 0
                print(f"Waiting for 10 seconds before restarting the transfer process for file '{filename}'...")
                time.sleep(10) # Wait for 10 seconds before restarting
            else:
                time.sleep(1)

    def retrigger(self, filename):
        self.acquire_lock_thread(filename)

if __name__ == "__main__":
    server_url = "http://localhost:8080"
    content_provider = ContentProvider(server_url, 8082, [('localhost', 8081)])
    lock_thread = threading.Thread(target=content_provider.acquire_lock_thread, args=("file1.txt",))
    lock_thread.start()

    try:
        while True:
            time.sleep(1) # Keep the main thread alive
    except KeyboardInterrupt:
        print("Terminating...")
