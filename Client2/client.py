import xmlrpc.client
import threading
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

class ClientFile:
    def __init__(self, nearby, client_ip, clients_port, message_passer):
        self.clients_port = clients_port
        self.client_ip = client_ip
        self.servers_nearby = nearby
        self.message_passer = message_passer
        self.mutex = threading.Lock()

    def get_files(self, filename):
        nearby_server = min(self.servers_nearby, key=self.servers_nearby.get)
        try:
            target_server = f"http://{nearby_server}:8080"
            proxy_server = xmlrpc.client.ServerProxy(target_server)
            message = Message(sender=self, receiver=proxy_server, content="REQUEST_FILE", filename=filename)
            self.message_passer.send_message(message)
            response = self.message_passer.receive_message()
            file_content = response.file_content
            if file_content != 'File not available':
                with open(filename, "wb") as file:
                    file.write(file_content.data)
                print(f"File '{filename}' is received from the Server {nearby_server} and has been saved locally.")
                return True
            else:
                print(f"File '{filename}' is not found on the available servers")
                return False
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return False

if __name__ == "__main__":
    current_ip = "localhost"
    client_port = 8000
    servers_nearby = {
        "localhost": 150,
        "localhost": 100,
    }

    message_passer = MessagePasser()

    client = ClientFile(servers_nearby, current_ip, client_port, message_passer)
    threading.Thread(target=message_passer.handle_messages).start()

    requestFile = input("Enter the required file name : ")
    if requestFile.find(".") != -1:
        if not requestFile.endswith("."):
            result = client.get_files(requestFile)
            if result:
                print("File has been received successfully")
            else:
                print("Error occurred while getting the requested file")
        else:
            print("file extension is not present - ensure we have the correct extension.")
    else:
        print("file extension is not present - ensure we have the correct extension.")
