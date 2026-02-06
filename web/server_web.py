# server_web.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI()

# Server state
class ServerState:
    def __init__(self):
        self.analytics_count = 0
        self.user_preferences = {}
        self.analytics_history = []
    
    def get_dump(self):
        return {
            "analytics_count": self.analytics_count,
            "user_preferences": self.user_preferences,
            "recent_analytics": self.analytics_history[-10:]  # Last 10 events
        }

state = ServerState()

# Request models
class AnalyticEvent(BaseModel):
    action: str
    target: str
    metadata: Optional[dict] = None

class RecommendationsRequest(BaseModel):
    user_id: str

# API Endpoints
@app.post("/api/analytic_event")
async def analytic_event(event: AnalyticEvent):
    """Handle analytic event - no response needed"""
    state.analytics_count += 1
    state.analytics_history.append({
        "action": event.action,
        "target": event.target,
        "metadata": event.metadata,
        "count": state.analytics_count
    })
    
    print(f"[Server] Analytics event: {event.action} on {event.target}")
    print(f"[Server] Count: {state.analytics_count}")
    
    return {
        "status": "ok",
        "analytics_count": state.analytics_count
    }

@app.post("/api/get_recommendations")
async def get_recommendations(request: RecommendationsRequest):
    """Get recommendations for a user"""
    print(f"[Server] Get recommendations for user: {request.user_id}")
    
    # Generate recommendations
    recommendations = [
        "Product A - Premium Widget",
        "Product B - Deluxe Gadget", 
        "Product C - Super Tool"
    ]
    
    # Update state
    state.user_preferences[request.user_id] = "last_recommended"
    
    return {
        "user_id": request.user_id,
        "recommendations": recommendations,
        "analytics_count": state.analytics_count
    }

@app.get("/api/state_dump")
async def state_dump():
    """Get complete state dump"""
    print("[Server] State dump requested")
    return state.get_dump()

@app.get("/api/reset")
async def reset_state():
    """Reset server state"""
    print("[Server] Resetting state")
    state.analytics_count = 0
    state.user_preferences = {}
    state.analytics_history = []
    return {"status": "reset", "message": "State has been reset"}

# Serve the HTML page
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Server Client</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        h1 {
            color: #2d3748;
            margin-bottom: 8px;
            font-size: 28px;
        }
        
        h2 {
            color: #4a5568;
            margin-bottom: 16px;
            font-size: 20px;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
        }
        
        .subtitle {
            color: #718096;
            margin-bottom: 24px;
            font-size: 14px;
        }
        
        .button-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button.secondary {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        }
        
        button.danger {
            background: linear-gradient(135deg, #f56565 0%, #c53030 100%);
        }
        
        .input-group {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
        }
        
        input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        #output {
            background: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .log-entry {
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .log-entry:last-child {
            border-bottom: none;
        }
        
        .log-time {
            color: #718096;
            font-size: 11px;
        }
        
        .log-success {
            color: #38a169;
        }
        
        .log-error {
            color: #e53e3e;
        }
        
        .log-info {
            color: #3182ce;
        }
        
        .status-bar {
            background: #edf2f7;
            padding: 12px 16px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            margin-bottom: 16px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #48bb78;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .loading {
            animation: pulse 1.5s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🚀 Python Server Client</h1>
            <p class="subtitle">Interactive demo of client-server communication</p>
            
            <div class="status-bar">
                <div class="status-item">
                    <span class="status-dot"></span>
                    <span>Server Connected</span>
                </div>
                <div class="status-item">
                    <span>Analytics: <strong id="analyticsCount">0</strong></span>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Analytic Events</h2>
            <div class="button-grid">
                <button onclick="sendAnalyticEvent('click', 'button_1')">Click Button 1</button>
                <button onclick="sendAnalyticEvent('click', 'button_2')">Click Button 2</button>
                <button onclick="sendAnalyticEvent('view', 'page_home')">View Home</button>
                <button onclick="sendAnalyticEvent('view', 'page_products')">View Products</button>
                <button onclick="sendAnalyticEvent('purchase', 'product_123')">Purchase Event</button>
                <button onclick="sendAnalyticEvent('scroll', 'section_features')">Scroll Event</button>
            </div>
        </div>
        
        <div class="card">
            <h2>🎯 Recommendations</h2>
            <div class="input-group">
                <input type="text" id="userId" placeholder="Enter user ID" value="user_123">
                <button class="secondary" onclick="getRecommendations()">Get Recommendations</button>
            </div>
        </div>
        
        <div class="card">
            <h2>💾 State Management</h2>
            <div class="button-grid">
                <button class="secondary" onclick="getStateDump()">📋 Dump State</button>
                <button class="danger" onclick="resetState()">🔄 Reset State</button>
            </div>
        </div>
        
        <div class="card">
            <h2>📝 Output Log</h2>
            <div id="output"></div>
        </div>
    </div>

    <script>
        const output = document.getElementById('output');
        const analyticsCountEl = document.getElementById('analyticsCount');
        
        function log(message, type = 'info') {
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `
                <span class="log-time">[${time}]</span>
                <span class="log-${type}">${message}</span>
            `;
            output.insertBefore(entry, output.firstChild);
        }
        
        async function sendAnalyticEvent(action, target) {
            try {
                log(`Sending analytic event: ${action} on ${target}...`, 'info');
                
                const response = await fetch('/api/analytic_event', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        action: action,
                        target: target,
                        metadata: { timestamp: Date.now() }
                    })
                });
                
                const data = await response.json();
                log(`✓ Event sent successfully. Total count: ${data.analytics_count}`, 'success');
                analyticsCountEl.textContent = data.analytics_count;
            } catch (error) {
                log(`✗ Error: ${error.message}`, 'error');
            }
        }
        
        async function getRecommendations() {
            const userId = document.getElementById('userId').value;
            
            if (!userId) {
                log('✗ Please enter a user ID', 'error');
                return;
            }
            
            try {
                log(`Requesting recommendations for ${userId}...`, 'info');
                
                const response = await fetch('/api/get_recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: userId
                    })
                });
                
                const data = await response.json();
                log(`✓ Recommendations for ${data.user_id}:`, 'success');
                data.recommendations.forEach(rec => {
                    log(`  • ${rec}`, 'success');
                });
            } catch (error) {
                log(`✗ Error: ${error.message}`, 'error');
            }
        }
        
        async function getStateDump() {
            try {
                log('Requesting state dump...', 'info');
                
                const response = await fetch('/api/state_dump');
                const data = await response.json();
                
                log('✓ Current State:', 'success');
                log(JSON.stringify(data, null, 2), 'success');
            } catch (error) {
                log(`✗ Error: ${error.message}`, 'error');
            }
        }
        
        async function resetState() {
            if (!confirm('Are you sure you want to reset all state?')) {
                return;
            }
            
            try {
                log('Resetting state...', 'info');
                
                const response = await fetch('/api/reset');
                const data = await response.json();
                
                log(`✓ ${data.message}`, 'success');
                analyticsCountEl.textContent = '0';
            } catch (error) {
                log(`✗ Error: ${error.message}`, 'error');
            }
        }
        
        // Log initial message
        log('Client initialized and ready', 'success');
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    print("[Server] Starting web server on http://localhost:8000")
    print("[Server] Open your browser to http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
