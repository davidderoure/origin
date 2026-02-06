# client_socket.py - Fixed shutdown handling
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
        self.listener_started = threading.Event()
        self.listener_stopped = threading.Event()
        self.send_lock = threading.Lock()
        self.listener_thread = None
    
    def connect(self):
        """Connect to Unix domain socket"""
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        print(f"[Client] Connecting to {self.socket_path}...")
        max_retries = 10
        for i in range(max_retries):
            try:
                self.socket.connect(self.socket_path)
                break
            except (FileNotFoundError, ConnectionRefusedError):
                if i < max_retries - 1:
                    print(f"[Client] Waiting for server... ({i+1}/{max_retries})")
                    time.sleep(1)
                else:
                    raise Exception("Could not connect to server")
        
        print("[Client] Connected!")
        self.running = True
        
        # Start listener thread
        self.listener_thread = threading.Thread(target=self._listen, daemon=False)
        self.listener_thread.start()
        
        # Wait for listener to be ready
        self.listener_started.wait(timeout=2)
        print("[Client] Listener thread ready")
    
    def _send_message(self, message):
        """Send a message (thread-safe)"""
        with self.send_lock:
            try:
                if not self.running:
                    return
                data = json.dumps(message).encode('utf-8')
                length_prefix = struct.pack('I', len(data))
                self.socket.sendall(length_prefix + data)
            except Exception as e:
                print(f"[Client] Error sending: {e}")
    
    def _receive_message(self):
        """Receive a message"""
        try:
            # Read exactly 4 bytes for length
            length_data = self._recv_exact(4)
            if not length_data:
                return None
            
            message_length = struct.unpack('I', length_data)[0]
            
            # Sanity check for message length
            if message_length > 10 * 1024 * 1024:  # 10MB max
                print(f"[Client] Invalid message length: {message_length}")
                return None
            
            # Read exactly message_length bytes
            data = self._recv_exact(message_length)
            if not data:
                return None
            
            return json.loads(data.decode('utf-8'))
        except socket.error as e:
            if self.running:
                print(f"[Client] Socket error receiving: {e}")
            return None
        except Exception as e:
            if self.running:
                print(f"[Client] Error receiving: {e}")
            return None
    
    def _recv_exact(self, num_bytes):
        """Receive exactly num_bytes from socket"""
        data = b''
        while len(data) < num_bytes:
            try:
                chunk = self.socket.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data += chunk
            except socket.error:
                if self.running:
                    raise
                return None
        return data
    
    def _listen(self):
        """Listen for server messages"""
        self.listener_started.set()
        
        try:
            while self.running:
                message = self._receive_message()
                if not message:
                    if self.running:
                        print("[Client] Server disconnected")
                    break
                
                msg_type = message.get('type')
                print(f"[Client] Received message type: {msg_type}")
                
                if msg_type == 'save_state':
                    print(f"[Client] Server requested state save:")
                    print(f"  {message.get('data')}")
                
                elif msg_type == 'recommendations_response':
                    request_id = message.get('request_id')
                    print(f"[Client] Got recommendations response for request {request_id}")
                    if request_id in self.pending_requests:
                        self.pending_requests[request_id]['result'] = message.get('data')
                        self.pending_requests[request_id]['event'].set()
        except Exception as e:
            if self.running:
                print(f"[Client] Listener error: {e}")
        finally:
            self.listener_stopped.set()
            print("[Client] Listener thread stopped")
    
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
        
        # Set up pending request BEFORE sending
        self.pending_requests[request_id] = {'event': event, 'result': None}
        
        message = {
            'type': 'get_recommendations',
            'request_id': request_id,
            'data': {'user_id': user_id}
        }
        self._send_message(message)
        print(f"[Client] Sent get_recommendations for {user_id}")
        
        # Wait for response
        if event.wait(timeout):
            result = self.pending_requests.pop(request_id)['result']
            print(f"[Client] Got recommendations: {result['recommendations']}")
            return result
        else:
            self.pending_requests.pop(request_id, None)
            raise TimeoutError(f"Request timed out after {timeout}s")
    
    def close(self):
        """Close connection gracefully"""
        print("[Client] Closing connection...")
        
        # Signal listener to stop
        self.running = False
        
        # Close socket to unblock any recv() calls
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.socket.close()
            except:
                pass
        
        # Wait for listener thread to finish
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_stopped.wait(timeout=2)
        
        print("[Client] Connection closed")

def main():
    client = SocketClient()
    
    try:
        client.connect()
        time.sleep(0.5)
        
        print("\n=== Sending analytic events ===")
        for i in range(7):
            client.send_analytic_event("click", f"button_{i}")
            time.sleep(0.5)
        
        print("\n=== Getting recommendations ===")
        try:
            recs = client.get_recommendations("user_123")
            print(f"[Main] Got: {recs}")
        except TimeoutError as e:
            print(f"[Main] Error: {e}")
        
        print("\n=== Sending more events ===")
        for i in range(3):
            client.send_analytic_event("view", f"page_{i}")
            time.sleep(0.5)
        
        time.sleep(2)
    
    finally:
        client.close()
    
    print("\n=== Done ===")

if __name__ == '__main__':
    main()
