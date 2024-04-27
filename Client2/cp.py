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

    def send_file(self, filename):
        print(f"Attempting to send file '{filename}'...")
        with open(filename, "rb") as file:
            file_content = xmlrpc.client.Binary(file.read())
            result = self.server_proxy.save_files(filename, file_content)
            if result == "Success":
                print(f"File '{filename}' sent successfully.")
            else:
                print(f"Error occurred while sending the required file '{filename}' to the server: {result}")

    def send_lock_request(self, filename):
        for peer in self.peers:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(peer)
            client_socket.sendall(f"REQUEST:{filename}".encode())
            client_socket.close()

    def send_lock_reply(self, filename):
        for peer in self.peers:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(peer)
            client_socket.sendall(f"REPLY:{filename}".encode())
            client_socket.close()

    def handle_lock_request(self, connection, address):
        data = connection.recv(1024).decode()
        if data.startswith("REQUEST:"):
            filename = data.split(":")[1]
            print(f"Received lock request for file '{filename}' from {address}.")
            self.send_lock_reply(filename)
            self.lock_acquired = True
        elif data.startswith("REPLY:"):
            print(f"Received lock reply from {address}.")
            self.lock_acquired = True

    def acquire_lock_thread(self, filename):
        while True:  # Keep the thread running indefinitely
            if not self.lock_acquired:
                self.send_lock_request(filename)
                while not self.lock_acquired:
                    connection, address = self.server_socket.accept()
                    self.handle_lock_request(connection, address)
                    connection.close()
                self.send_file(filename)
                # Release the lock here
                self.send_lock_reply(filename)  # Assuming this acts as a lock release signal
                self.lock_acquired = False
            else:
                # Optionally, add a delay here to reduce CPU usage
                time.sleep(1)

    def content_provider(self, filename):
        while True:
            self.acquire_lock_thread(filename)

if __name__ == "__main__":
    server_url = "http://localhost:8080"
    time.sleep(5)
    content_provider = ContentProvider(server_url, 8082, [('localhost', 8081)])
    lock_thread = threading.Thread(target=content_provider.acquire_lock_thread, args=("file1.txt",))
    lock_thread.start()
    lock_thread.join()
