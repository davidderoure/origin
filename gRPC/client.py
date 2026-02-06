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
    
    async def _listen_for_server_messages
