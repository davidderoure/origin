# client_pipe.py - Windows Named Pipes Client
import win32file
import win32pipe
import pywintypes
import json
import struct
import threading
import uuid
import time

class PipeClient:
    def __init__(self, pipe_name=r'\\.\pipe\PythonServerPipe'):
        self.pipe_name = pipe_name
        self.pipe_handle = None
        self.pending_requests = {}
        self.running = False
    
    def connect(self):
        """Connect to the named pipe server"""
        print(f"[Client] Connecting to {self.pipe_name}...")
        
        # Wait for pipe to be available
        while True:
            try:
                self.pipe_handle = win32file.CreateFile(
                    self.pipe_name,
                    win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                    0,
                    None,
                    win32file.OPEN_EXISTING,
                    0,
                    None
                )
                break
            except pywintypes.error as e:
                if e.args[0] == 2:  # ERROR_FILE_NOT_FOUND
                    print("[Client] Waiting for server...")
                    time.sleep(1)
                else:
                    raise
        
        # Set pipe to message mode
        win32pipe.SetNamedPipeHandleState(
            self.pipe_handle,
            win32pipe.PIPE_READMODE_MESSAGE,
            None,
            None
        )
        
        print("[Client] Connected!")
        self.running = True
        
        # Start listening for server messages
        listener_thread = threading.Thread(target=self._listen, daemon=True)
        listener_thread.start()
    
    def _send_message(self, message):
        """Send a message through the pipe"""
        data = json.dumps(message).encode('utf-8')
        length_prefix = struct.pack('I', len(data))
        win32file.WriteFile(self.pipe_handle, length_prefix + data)
    
    def _receive_message(self):
        """Receive a message from the pipe"""
        # Read length prefix
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
        """Listen for messages from server"""
        try:
            while self.running:
                message = self._receive_message()
                if not message:
                    break
                
                self._handle_message(message)
        except pywintypes.error as e:
            print(f"[Client] Pipe error: {e}")
    
    def _handle_message(self, message):
        """Handle incoming message from server"""
        msg_type = message.get('type')
        
        if msg_type == 'save_state':
            self._handle_save_state(message.get('data'))
        
        elif msg_type == 'recommendations_response':
            request_id = message.get('request_id')
            if request_id in self.pending_requests:
                self.pending_requests[request_id]['result'] = message.get('data')
                self.pending_requests[request_id]['event'].set()
    
    def _handle_save_state(self, state_data):
        """Handle save state request from server"""
        print(f"[Client] Server requested state save:")
        print(f"  {state_data}")
        print("[Client] Would save to database...")
    
    def send_analytic_event(self, action, target):
        """Send analytic event (no response expected)"""
        message = {
            'type': 'analytic_event',
            'data': {
                'action': action,
                'target': target
            }
        }
        self._send_message(message)
        print(f"[Client] Sent analytic event: {action} on {target}")
    
    def get_recommendations(self, user_id, timeout=5.0):
        """Get recommendations (waits for response)"""
        request_id = str(uuid.uuid4())
        
        # Create event to wait for response
        event = threading.Event()
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
        """Close the connection"""
        self.running = False
        if self.pipe_handle:
            win32file.CloseHandle(self.pipe_handle)
        print("[Client] Connection closed")

def main():
    client = PipeClient()
    client.connect()
    
    time.sleep(0.1)
    
    print("\n=== Sending analytic events ===")
    for i in range(7):
        client.send_analytic_event("click", f"button_{i}")
        time.sleep(0.5)
    
    print("\n=== Getting recommendations ===")
    recommendations = client.get_recommendations("user_123")
    print(f"[Main] Got recommendations: {recommendations}")
    
    print("\n=== Sending more events ===")
    for i in range(3):
        client.send_analytic_event("view", f"page_{i}")
        time.sleep(0.5)
    
    time.sleep(2)
    client.close()
    print("\n=== Done ===")

if __name__ == '__main__':
    main()
