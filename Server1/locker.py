import threading
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class LockServer:
    def __init__(self, server_id):
        self.server_id = server_id
        self.lock = threading.Lock()

    def acquire_lock(self):
        acquired = self.lock.acquire(blocking=False)
        return acquired

    def release_lock(self):
        self.lock.release()
        return True

    def serve(self):
        server = SimpleXMLRPCServer(self.server_id, requestHandler=RequestHandler, allow_none=True)
        server.register_instance(self)
        print(f"Lock Server on {self.server_id} has been started")
        server.serve_forever()


if __name__ == "__main__":
    PORT = 8081
    CURRENT_IP = "localhost"
    lock_server = LockServer((CURRENT_IP, PORT))
    lock_server.serve()
