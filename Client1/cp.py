import threading
import time
import xmlrpc.client
import xmlrpc.server


class ContentProvider:
    def __init__(self, file_srv_url, current_ip, port, peers):
        self.initd_lock_rqst = None
        self.server_proxy = xmlrpc.client.ServerProxy(file_srv_url)
        self.port = port
        self.peers = peers
        self.lock_acqrd = False
        self.rqsts_rcvd = 0
        self.lock = threading.Lock()
        self.current_ip = current_ip

        self.server = xmlrpc.server.SimpleXMLRPCServer((current_ip, self.port), allow_none=True)
        self.server.register_introspection_functions()
        self.server.register_instance(self)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def send_file(self, filename):
        print(f"beginning to upload the file '{filename}'...")
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

    def send_lock_rqst(self, filename):
        for peer in self.peers:
            try:
                with xmlrpc.client.ServerProxy(f"http://{peer[0]}:{peer[1]}/") as proxy:
                    proxy.handle_lock_rqst(filename)
            except Exception as e:
                print(f"waiting for {peer}....")
                time.sleep(5)

    def lock_stats_rspnd(self, filename):
        for peer in self.peers:
            try:
                with xmlrpc.client.ServerProxy(f"http://{peer[0]}:{peer[1]}/") as proxy:
                    proxy.handle_lock_reply(filename)
            except Exception as e:
                print(f"waiting for {peer}...")
                time.sleep(5)

    def handle_lock_rqst(self, filename):
        try:
            with self.lock:
                self.lock_stats_rspnd(filename)
                self.rqsts_rcvd += 1
                if self.rqsts_rcvd == len(self.peers):
                    self.lock_acqrd = True
                    print(f"Lock acquired")
                else:
                    print("request received exceeds peers list")
        except Exception as e:
            print(f"Errors under handle lock rqst: {e}")

    def handle_lock_reply(self, filename):
        print(f"Received lock trigger for file")
        with self.lock:
            if self.initd_lock_rqst:  # Check if this instance requested the lock
                self.rqsts_rcvd += 1
                if self.rqsts_rcvd == len(self.peers):
                    self.lock_acqrd = False
                    self.initd_lock_rqst = False  # Reset flag
                    print(f"Lock released for file")
            else:
                print(f"Ignoring lock trigger for file '{filename}'.")

    def ack_lock(self, filename):
        while True:  # indefinite search until locks are achieved
            if not self.lock_acqrd:
                self.send_lock_rqst(filename)  # send lock request for files
                while not self.lock_acqrd:
                    time.sleep(1)  # waiting for replies
                self.send_file(filename)
                print(f"Lock released for file '{filename}'.")
                with self.lock:
                    self.lock_acqrd = False
                    self.rqsts_rcvd = 0
                print(f"restarting the process to sync the files with server '{filename}'...")
                self.send_lock_rqst(filename)  # send lock request for files
                time.sleep(10)  # Wait for 10 seconds before restarting
            else:
                time.sleep(1)


if __name__ == "__main__":
    server_url = "http://172.31.12.87:8080"
    current_ip = "172.31.11.56"
    content_provider = ContentProvider(server_url, current_ip,8081, [('172.31.4.249', 8082), ('172.31.4.249', 8083)])
    lock_thread = threading.Thread(target=content_provider.ack_lock, args=("file1.txt",))
    lock_thread.daemon = True  # Set the thread as daemon to stop with the main thread
    lock_thread.start()  # thread start for the starting the lock

    try:
        while True:
            time.sleep(1)  # Keeping the initial thread active
    except KeyboardInterrupt:  # Key Interrupt handling
        print("Terminating...")
