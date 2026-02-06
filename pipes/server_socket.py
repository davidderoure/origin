# server_socket.py - Cross-platform using Unix Domain Sockets
import socket
import json
import struct
import os
import threading

class SocketServer:
    def __init__(self, socket_path='/tmp/python_server.sock'):
        self.socket_path = socket_path
        self.analytics_count = 0
        self.user_preferences = {}
        self.client_socket = None
        self.running = False
    
    def start(self):
        """Start the Unix domain socket server"""
        # Remove existing socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_socket.bind(self.socket_path)
        server_socket.listen(1)
        
        print(f"[Server] Listening on {self.socket_path}")
        
        self.client_socket, _ = server_socket.accept()
        print("[Server] Client connected!")
        
        self.running = True
        self._listen()
    
    def _send_message(self, message):
        """Send a message with length prefix"""
        data = json.dumps(message).encode('utf-8')
        length_prefix = struct.pack('I', len(data))
        self.client_socket.sendall(length_prefix + data)
        print(f"[Server] Sent: {message.get('type')}")
    
    def _receive_message(self):
        """Receive a message"""
        # Read length prefix
        length_data = self.client_socket.recv(4)
        if len(length_data) < 4:
            return None
        
        message_length = struct.unpack('I', length_data)[0]
        
        # Read the message
        data = b''
        while len(data) < message_length:
            chunk = self.client_socket.recv(message_length - len(data))
            if not chunk:
                return None
            data += chunk
        
        return json.loads(data.decode('utf-8'))
    
    def _listen(self):
        """Listen for client messages"""
        try:
            while self.running:
                message = self._receive_message()
                if not message:
                    break
                
                msg_type = message.get('type')
                data = message.get('data', {})
                
                print(f"[Server] Received: {msg_type}")
                
                if msg_type == 'analytic_event':
                    self.analytics_count += 1
                    print(f"[Server] Analytics count: {self.analytics_count}")
                    
                    if self.analytics_count % 5 == 0:
                        self._send_save_state()
                
                elif msg_type == 'get_recommendations':
                    user_id = data.get('user_id')
                    request_id = data.get('request_id')
                    
                    response = {
                        'type': 'recommendations_response',
                        'request_id': request_id,
                        'data': {
                            'user_id': user_id,
                            'recommendations': ['Product A', 'Product B', 'Product C']
                        }
                    }
                    self._send_message(response)
                    
                    self.user_preferences[user_id] = 'last_recommended'
                    self._send_save_state()
        except Exception as e:
            print(f"[Server] Error: {e}")
        finally:
            self.stop()
    
    def _send_save_state(self):
        """Send save state request"""
        state_message = {
            'type': 'save_state',
            'data': {
                'analytics_count': self.analytics_count,
                'user_preferences': self.user_preferences
            }
        }
        self._send_message(state_message)
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        print("[Server] Stopped")

if __name__ == '__main__':
    server = SocketServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")
        server.stop()
