# server_pipe.py - Windows Named Pipes Server
import win32pipe
import win32file
import pywintypes
import json
import struct
import threading

class PipeServer:
    def __init__(self, pipe_name=r'\\.\pipe\PythonServerPipe'):
        self.pipe_name = pipe_name
        self.analytics_count = 0
        self.user_preferences = {}
        self.pipe_handle = None
        self.running = False
    
    def start(self):
        """Start the named pipe server"""
        print(f"[Server] Creating named pipe: {self.pipe_name}")
        
        self.pipe_handle = win32pipe.CreateNamedPipe(
            self.pipe_name,
            win32pipe.PIPE_ACCESS_DUPLEX,  # Bidirectional
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
            1,  # Max instances
            65536,  # Out buffer size
            65536,  # In buffer size
            0,  # Default timeout
            None  # Security attributes
        )
        
        print("[Server] Waiting for client connection...")
        win32pipe.ConnectNamedPipe(self.pipe_handle, None)
        print("[Server] Client connected!")
        
        self.running = True
        
        # Start listening for messages
        self._listen()
    
    def _send_message(self, message):
        """Send a message through the pipe with length prefix"""
        data = json.dumps(message).encode('utf-8')
        # Send length prefix (4 bytes) followed by data
        length_prefix = struct.pack('I', len(data))
        win32file.WriteFile(self.pipe_handle, length_prefix + data)
        print(f"[Server] Sent: {message.get('type')}")
    
    def _receive_message(self):
        """Receive a message from the pipe"""
        # Read length prefix (4 bytes)
        result, length_data = win32file.ReadFile(self.pipe_handle, 4)
        if result != 0:
            return None
        
        message_length = struct.unpack('I', length_data)[0]
        
        # Read the actual message
        result, data = win32file.ReadFile(self.pipe_handle, message_length)
        if result != 0:
            return None
        
        return json.loads(data.decode('utf-8'))
    
    def _listen(self):
        """Listen for messages from client"""
        try:
            while self.running:
                message = self._receive_message()
                if not message:
                    break
                
                self._handle_message(message)
        except pywintypes.error as e:
            print(f"[Server] Pipe error: {e}")
        finally:
            self.stop()
    
    def _handle_message(self, message):
        """Handle incoming message from client"""
        msg_type = message.get('type')
        data = message.get('data', {})
        
        print(f"[Server] Received: {msg_type}")
        
        if msg_type == 'analytic_event':
            self.analytics_count += 1
            print(f"[Server] Analytics count: {self.analytics_count}")
            
            # Save state every 5 events
            if self.analytics_count % 5 == 0:
                self._send_save_state()
        
        elif msg_type == 'get_recommendations':
            user_id = data.get('user_id')
            request_id = data.get('request_id')
            
            # Send recommendations response
            response = {
                'type': 'recommendations_response',
                'request_id': request_id,
                'data': {
                    'user_id': user_id,
                    'recommendations': ['Product A', 'Product B', 'Product C']
                }
            }
            self._send_message(response)
            
            # Update state and save
            self.user_preferences[user_id] = 'last_recommended'
            self._send_save_state()
    
    def _send_save_state(self):
        """Send save state request to client"""
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
        if self.pipe_handle:
            win32file.CloseHandle(self.pipe_handle)
        print("[Server] Stopped")

if __name__ == '__main__':
    server = PipeServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")
        server.stop()
