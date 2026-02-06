# client.py
import asyncio
import websockets
import json
from typing import Optional
import uuid

class PythonClient:
    def __init__(self, url: str = "ws://127.0.0.1:8000/ws"):
        self.url = url
        self.websocket = None
        self.pending_requests = {}  # Track requests waiting for responses
        
    async def connect(self):
        """Connect to the server"""
        self.websocket = await websockets.connect(self.url)
        print("[Client] Connected to server")
        
        # Start listening for messages in background
        asyncio.create_task(self._listen_for_messages())
    
    async def _listen_for_messages(self):
        """Listen for server messages (responses and callbacks)"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "save_state":
                    # Server is calling us to save state
                    await self._handle_save_state(data.get("data"))
                
                elif msg_type == "recommendations_response":
                    # Response to our get_recommendations request
                    request_id = data.get("request_id")
                    if request_id in self.pending_requests:
                        # Wake up the waiting coroutine
                        self.pending_requests[request_id].set_result(data.get("data"))
                
                else:
                    print(f"[Client] Received unknown message type: {msg_type}")
        
        except websockets.exceptions.ConnectionClosed:
            print("[Client] Connection closed")
    
    async def _handle_save_state(self, state_data):
        """Handle save_state callback from server"""
        print(f"[Client] Server requested state save: {state_data}")
        # In C#, this would call your backend to persist the state
        # For now, just print it
        print(f"[Client] Would save to database: {json.dumps(state_data, indent=2)}")
    
    async def send_analytic_event(self, event_data: dict):
        """Send analytic event - no response expected"""
        message = {
            "type": "analytic_event",
            "data": event_data
        }
        await self.websocket.send(json.dumps(message))
        print(f"[Client] Sent analytic event: {event_data}")
    
    async def get_recommendations(self, user_id: str) -> dict:
        """Send get_recommendations request - wait for response"""
        request_id = str(uuid.uuid4())
        
        # Create a future to wait for the response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        message = {
            "type": "get_recommendations",
            "request_id": request_id,
            "data": {"user_id": user_id}
        }
        await self.websocket.send(json.dumps(message))
        print(f"[Client] Sent get_recommendations for user {user_id}")
        
        # Wait for response (with timeout)
        try:
            result = await asyncio.wait_for(future, timeout=5.0)
            print(f"[Client] Received recommendations: {result}")
            return result
        finally:
            del self.pending_requests[request_id]
    
    async def close(self):
        """Close connection"""
        if self.websocket:
            await self.websocket.close()

async def main():
    """Example usage"""
    client = PythonClient()
    await client.connect()
    
    # Give the listener task a moment to start
    await asyncio.sleep(0.1)
    
    # Send some analytic events (no response)
    for i in range(7):
        await client.send_analytic_event({"action": "click", "button": f"button_{i}"})
        await asyncio.sleep(0.5)
    
    # Get recommendations (with response)
    recommendations = await client.get_recommendations("user_123")
    print(f"[Main] Got recommendations: {recommendations}")
    
    # Send more analytics to trigger another save
    for i in range(3):
        await client.send_analytic_event({"action": "view", "page": f"page_{i}"})
        await asyncio.sleep(0.5)
    
    # Keep connection open to receive any final messages
    await asyncio.sleep(2)
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
