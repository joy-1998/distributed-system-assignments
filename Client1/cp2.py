import xmlrpc.client
import threading
import time
import hashlib
import queue

class Message:
    def __init__(self, sender, receiver, content, filename=None, file_content=None):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.filename = filename
        self.file_content = file_content

class MessagePasser:
    def __init__(self):
        self.inbox = queue.Queue()
        self.outbox = queue.Queue()
        self.mutex = threading.Lock()

    def send_message(self, message):
        with self.mutex:
            self.outbox.put(message)

    def receive_message(self):
        if not self.inbox.empty():
            return self.inbox.get()
        return None

    def handle_messages(self):
        while True:
            if not self.outbox.empty():
                message = self.outbox.get()
                message.receiver.inbox.put(message)

class ContentProviders:
    def __init__(self, available_servers, message_passer):
        self.server_list = available_servers
        self.message_passer = message_passer
        self.mutex = threading.Lock()

    def send_files(self, filename):
        try:
            with open(filename, "rb") as file:
                file_content = xmlrpc.client.Binary(file.read())
            for server in self.server_list:
                server_proxy = xmlrpc.client.ServerProxy(server)
                message = Message(sender=self, receiver=server_proxy, content="SAVE_FILE", filename=filename, file_content=file_content)
                self.message_passer.send_message(message)
                print(f"File '{filename}' transmitted to server at {server}")
        except FileNotFoundError:
            print(f"File '{filename}' not available, please try again.")
        except Exception as e:
            print(f"Error occurred while sending the file '{filename}': {str(e)}")

    def content_provider(self, filename):
        while True:
            self.send_files(filename)
            time.sleep(120)

if __name__ == "__main__":
    server_list = ["http://localhost:8080"]

    message_passer = MessagePasser()
    content_provider = ContentProviders(server_list, message_passer)

    threading.Thread(target=message_passer.handle_messages).start()
    content_provider.content_provider('file1.txt')
