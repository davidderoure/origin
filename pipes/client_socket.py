# client_socket.py
import socket
import json
import struct
import threading
import uuid
import time

class SocketClient:
    def __init__(self, socket_path='/tmp/python_server.sock'):
        self.socket_path = socket_path
        self.socket = None
        self.pending_requests = {}
        self.running = False
    
    def connect(self):
        """Connect to Unix domain socket"""
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        print(f"[Client] Connecting to {self.socket_path}...")
        while True:
            try:
                self.socket.connect(self.socket_path)
                break
            except FileNotFoundError:
                print("[Client] Waiting for server...")
                time.sleep(1)
        
        print("[Client] Connected!")
        self.running = True
        
        listener_thread = threading.Thread(target=self._listen, daemon=True)
        listener_thread.start()
    
    def _send_message(self, message):
        """Send a message"""
        data = json.dumps(message).encode('utf-8')
        length_prefix = struct.pack('I', len(data))
        self.socket.sendall(length_prefix + data)
    
    def _receive_message(self):
        """Receive a message"""
        length_data = self.socket.recv(4)
        if len(length_data) < 4:
            return None
        
        message_length = struct.unpack('I', length_data)[0]
        
        data = b''
        while len(data) < message_length:
            chunk = self.socket.recv(message_length - len(data))
            if not chunk:
                return None
            data += chunk
        
        return json.loads(data.decode('utf-8'))
    
    def _listen(self):
        """Listen for server messages"""
        try:
            while self.running:
                message = self._receive_message()
                if not message:
                    break
                
                msg_type = message.get('type')
                
                if msg_type == 'save_state':
                    print(f"[Client] Server requested state save:")
                    print(f"  {message.get('data')}")
                
                elif msg_type == 'recommendations_response':
                    request_id = message.get('request_id')
                    if request_id in self.pending_requests:
                        self.pending_requests[request_id]['result'] = message.get('data')
                        self.pending_requests[request_id]['event'].set()
        except Exception as e:
            print(f"[Client] Error: {e}")
    
    def send_analytic_event(self, action, target):
        """Send analytic event"""
        message = {
            'type': 'analytic_event',
            'data': {'action': action, 'target': target}
        }
        self._send_message(message)
        print(f"[Client] Sent analytic event: {action} on {target}")
    
    def get_recommendations(self, user_id, timeout=5.0):
        """Get recommendations"""
        request_id = str(uuid.uuid4())
        event = threading.Event()
        self.pending_requests[request_id] = {'event': event, 'result': None}
        
        message = {
            'type': 'get_recommendations',
            'request_id': request_id,
            'data': {'user_id': user_id}
        }
        self._send_message(message)
        print(f"[Client] Sent get_recommendations for {user_id}")
        
        if event.wait(timeout):
            result = self.pending_requests.pop(request_id)['result']
            print(f"[Client] Got recommendations: {result['recommendations']}")
            return result
        else:
            self.pending_requests.pop(request_id, None)
            raise TimeoutError("Request timed out")
    
    def close(self):
        """Close connection"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("[Client] Connection closed")

def main():
    client = SocketClient()
    client.connect()
    time.sleep(0.1)
    
    print("\n=== Sending analytic events ===")
    for i in range(7):
        client.send_analytic_event("click", f"button_{i}")
        time.sleep(0.5)
    
    print("\n=== Getting recommendations ===")
    recs = client.get_recommendations("user_123")
    print(f"[Main] Got: {recs}")
    
    time.sleep(2)
    client.close()

if __name__ == '__main__':
    main()
