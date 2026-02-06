# client.py
import grpc
import asyncio
import contract_pb2
import contract_pb2_grpc
from typing import Dict
import uuid

class PythonClient:
    def __init__(self, address: str = "localhost:50051"):
        self.address = address
        self.channel = None
        self.stub = None
        self.stream = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
    
    async def connect(self):
        """Connect to the gRPC server"""
        self.channel = grpc.aio.insecure_channel(self.address)
        self.stub = contract_pb2_grpc.EventServiceStub(self.channel)
        
        # Start bidirectional stream
        self.stream = self.stub.EventStream()
        
        print("[Client] Connected to server")
        
        # Start listening for server messages in background
        asyncio.create_task(self._listen_for_server_messages())
    
    async def _listen_for_server_messages(self):
        """Listen for messages from the server"""
        try:
            async for server_msg in self.stream:
                if server_msg.HasField('recommendations_response'):
                    self._handle_recommendations_response(server_msg.recommendations_response)
                elif server_msg.HasField('save_state'):
                    await self._handle_save_state(server_msg.save_state)
                else:
                    print("[Client] Received unknown message type")
        except grpc.aio.AioRpcError as e:
            print(f"[Client] Stream error: {e.code()}")
        except Exception as e:
            print(f"[Client] Error listening: {e}")
    
    def _handle_recommendations_response(self, response):
        """Handle recommendations response from server"""
        request_id = response.request_id
        if request_id in self.pending_requests:
            future = self.pending_requests.pop(request_id)
            future.set_result(response)
            print(f"[Client] Received recommendations for {response.user_id}")
    
    async def _handle_save_state(self, save_state):
        """Handle save state request from server"""
        print(f"[Client] Server requested state save:")
        print(f"  Analytics count: {save_state.analytics_count}")
        print(f"  User preferences: {dict(save_state.user_preferences)}")
        
        # In real app, this would save to your database
        print(f"[Client] Would save to database...")
    
    async def send_analytic_event(self, action: str, target: str, metadata: dict = None):
        """Send an analytic event (no response expected)"""
        event = contract_pb2.AnalyticEvent(
            action=action,
            target=target
        )
        
        if metadata:
            event.metadata.update(metadata)
        
        message = contract_pb2.ClientMessage(analytic_event=event)
        await self.stream.write(message)
        print(f"[Client] Sent analytic event: {action} on {target}")
    
    async def get_recommendations(self, user_id: str, timeout: float = 5.0):
        """Get recommendations (waits for response)"""
        request_id = str(uuid.uuid4())
        
        # Create future to wait for response
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        request = contract_pb2.GetRecommendationsRequest(
            request_id=request_id,
            user_id=user_id
        )
        
        message = contract_pb2.ClientMessage(get_recommendations=request)
        await self.stream.write(message)
        print(f"[Client] Sent get_recommendations for {user_id}")
        
        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            print(f"[Client] Got recommendations: {list(response.recommendations)}")
            return response
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise TimeoutError(f"Request {request_id} timed out after {timeout}s")
    
    async def close(self):
        """Close the connection"""
        if self.stream:
            await self.stream.done_writing()
        if self.channel:
            await self.channel.close()
        print("[Client] Connection closed")

async def main():
    """Example usage"""
    client = PythonClient()
    await client.connect()
    
    # Give listener a moment to start
    await asyncio.sleep(0.1)
    
    print("\n=== Sending analytic events ===")
    # Send some analytic events (no response expected)
    for i in range(7):
        await client.send_analytic_event(
            action="click",
            target=f"button_{i}",
            metadata={"session": "test123"}
        )
        await asyncio.sleep(0.5)
    
    print("\n=== Getting recommendations ===")
    # Get recommendations (with response)
    recommendations = await client.get_recommendations("user_123")
    print(f"[Main] Received {len(recommendations.recommendations)} recommendations:")
    for rec in recommendations.recommendations:
        print(f"  - {rec}")
    
    print("\n=== Sending more events ===")
    # Send more analytics to trigger another save
    for i in range(3):
        await client.send_analytic_event(
            action="view",
            target=f"page_{i}"
        )
        await asyncio.sleep(0.5)
    
    # Keep connection open to receive any final messages
    await asyncio.sleep(2)
    
    await client.close()
    print("\n=== Done ===")

if __name__ == "__main__":
    asyncio.run(main())
