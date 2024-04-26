# Import Statements needed for content provider to function
import xmlrpc.client
import threading
import time


class ContentProvider:
    def __init__(self, file_srv_url):
        self.server_proxy = xmlrpc.client.ServerProxy(file_srv_url)

    def send_file(self, filename):
        print(f"Attempting to send file '{filename}'...")
        with open(filename, "rb") as file:
            file_content = xmlrpc.client.Binary(file.read())
            result = self.server_proxy.save_files(filename, file_content)
            if result == "Success":
                print(f"File '{filename}' sent successfully.")
            else:
                print(f"Error occurred while sending the required file "
                      f"'{filename}' to the server {server}: {result}")

    def acquire_lock_thread(self, filename):
        while True:
            result = self.server_proxy.acquire_lock()
            if result:
                try:
                    print(f"Lock acquired for file '{filename}'.")
                    self.send_file(filename)
                finally:
                    time.sleep(10)
                    self.server_proxy.release_lock()
                    print(f"Lock released for file '{filename}'.")
                    self.content_provider(filename)
            else:
                print("Lock not available. Waiting...")
                time.sleep(10)

    def content_provider(self, filename):
        while True:
            self.acquire_lock_thread(filename)


if __name__ == "__main__":
    server_url = "http://localhost:8080"
    content_provider = ContentProvider(server_url)
    lock_thread = threading.Thread(target=content_provider.acquire_lock_thread, args=("file2.txt",))
    lock_thread.start()
    lock_thread.join()
