# server.py
import grpc
from concurrent import futures
import asyncio
import contract_pb2
import contract_pb2_grpc

class EventServiceServicer(contract_pb2_grpc.EventServiceServicer):
    def __init__(self):
        self.analytics_count = 0
        self.user_preferences = {}
    
    async def EventStream(self, request_iterator, context):
        """Bidirectional streaming - handle messages and send responses"""
        
        async def send_save_state():
            """Helper to send save state request to client"""
            save_state = contract_pb2.SaveStateRequest(
                analytics_count=self.analytics_count,
                user_preferences=self.user_preferences
            )
            return contract_pb2.ServerMessage(save_state=save_state)
        
        # Process incoming messages
        async for client_msg in request_iterator:
            
            if client_msg.HasField('analytic_event'):
                # Handle analytic event
                event = client_msg.analytic_event
                self.analytics_count += 1
                print(f"[Server] Analytics event: {event.action} on {event.target}")
                print(f"[Server] Count: {self.analytics_count}")
                
                # Save state every 5 events
                if self.analytics_count % 5 == 0:
                    yield await send_save_state()
            
            elif client_msg.HasField('get_recommendations'):
                # Handle recommendations request
                req = client_msg.get_recommendations
                print(f"[Server] Get recommendations for user: {req.user_id}")
                
                # Generate recommendations
                response = contract_pb2.RecommendationsResponse(
                    request_id=req.request_id,
                    user_id=req.user_id,
                    recommendations=["Product A", "Product B", "Product C"]
                )
                yield contract_pb2.ServerMessage(recommendations_response=response)
                
                # Update state and save
                self.user_preferences[req.user_id] = "last_recommended"
                yield await send_save_state()

async def serve():
    server = grpc.aio.server()
    contract_pb2_grpc.add_EventServiceServicer_to_server(
        EventServiceServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    await server.start()
    print("[Server] gRPC server started on port 50051")
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
