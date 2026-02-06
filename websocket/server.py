# server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import asyncio
import json

app = FastAPI()

class ServerState:
    """Server maintains its own state"""
    def __init__(self):
        self.analytics_count = 0
        self.user_preferences = {}
        self.websocket = None
    
    async def save_state_to_client(self):
        """Server initiates a save state call to client"""
        if self.websocket:
            state_data = {
                "analytics_count": self.analytics_count,
                "user_preferences": self.user_preferences
            }
            message = {
                "type": "save_state",
                "data": state_data
            }
            await self.websocket.send_json(message)
            print(f"[Server] Saved state to client: {state_data}")

state = ServerState()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.websocket = websocket
    print("[Server] Client connected")
    
    try:
        while True:
            # Receive event from client
            message = await websocket.receive_json()
            event_type = message.get("type")
            data = message.get("data", {})
            
            print(f"[Server] Received event: {event_type}")
            
            if event_type == "analytic_event":
                # Handle analytics - no response needed
                state.analytics_count += 1
                print(f"[Server] Analytics count: {state.analytics_count}")
                
                # Save state every 5 events (example trigger)
                if state.analytics_count % 5 == 0:
                    await state.save_state_to_client()
            
            elif event_type == "get_recommendations":
                # Handle recommendation request - needs response
                user_id = data.get("user_id")
                recommendations = [
                    "Product A",
                    "Product B",
                    "Product C"
                ]
                
                response = {
                    "type": "recommendations_response",
                    "request_id": message.get("request_id"),
                    "data": {
                        "user_id": user_id,
                        "recommendations": recommendations
                    }
                }
                await websocket.send_json(response)
                print(f"[Server] Sent recommendations for user {user_id}")
                
                # Maybe save state after recommendations
                state.user_preferences[user_id] = "last_recommended"
                await state.save_state_to_client()
            
            else:
                print(f"[Server] Unknown event type: {event_type}")
    
    except WebSocketDisconnect:
        print("[Server] Client disconnected")
        state.websocket = None

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
