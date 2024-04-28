# Import Statements needed for client to function
import xmlrpc.client


class ClientFile:

    def __init__(self, nearby, client_ip, clients_port):
        self.clients_port = clients_port
        self.client_ip = client_ip
        self.servers_nearby = nearby

    def get_files(self, filename):
        nearby_server = min(self.servers_nearby,
                            key=self.servers_nearby.get)  # Minimum distance calculation based on the assumed values
        try:
            target_server = f"http://{nearby_server}:8080"
            # once nearby server has been identified it is used to make a call here
            proxy_server = xmlrpc.client.ServerProxy(target_server)  # xml rpc server connect
            file_content = proxy_server.get_files(filename)
            if file_content != 'File not available':  # file to write the received files in the clients local
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
    current_ip = "172.31.4.249"  # Current Clients ip locations
    client_port = 8000
    servers_nearby = {  # This dictionary declaration is made here as an assumption that the server distances are known
        "172.31.12.87": 150,
        "172.31.12.87": 100,
    }
    client = ClientFile(servers_nearby, current_ip, client_port)
    requestFile = input("Enter the required file name : ")  # Input declaration to receive the file input from the user
    if requestFile.find(".") != -1:  # Error handling if the entered file is not of the correct format
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
