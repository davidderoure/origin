// PythonServerClient.cs
using System;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

public class PythonServerClient : IDisposable
{
    private readonly ClientWebSocket _webSocket;
    private readonly string _url;
    private readonly CancellationTokenSource _cancellationTokenSource;
    private readonly ConcurrentDictionary<string, TaskCompletionSource<JsonElement>> _pendingRequests;
    
    public event EventHandler<StateData> OnSaveStateRequested;
    
    public PythonServerClient(string url = "ws://127.0.0.1:8000/ws")
    {
        _url = url;
        _webSocket = new ClientWebSocket();
        _cancellationTokenSource = new CancellationTokenSource();
        _pendingRequests = new ConcurrentDictionary<string, TaskCompletionSource<JsonElement>>();
    }
    
    public async Task ConnectAsync()
    {
        await _webSocket.ConnectAsync(new Uri(_url), _cancellationTokenSource.Token);
        Console.WriteLine("[Client] Connected to server");
        
        // Start listening for messages in background
        _ = Task.Run(ListenForMessagesAsync);
    }
    
    private async Task ListenForMessagesAsync()
    {
        var buffer = new byte[4096];
        var messageBuilder = new StringBuilder();
        
        try
        {
            while (_webSocket.State == WebSocketState.Open)
            {
                WebSocketReceiveResult result;
                messageBuilder.Clear();
                
                do
                {
                    result = await _webSocket.ReceiveAsync(
                        new ArraySegment<byte>(buffer), 
                        _cancellationTokenSource.Token);
                    
                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await _webSocket.CloseAsync(
                            WebSocketCloseStatus.NormalClosure, 
                            "Closing", 
                            CancellationToken.None);
                        Console.WriteLine("[Client] Connection closed by server");
                        return;
                    }
                    
                    var messageChunk = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    messageBuilder.Append(messageChunk);
                }
                while (!result.EndOfMessage);
                
                var messageJson = messageBuilder.ToString();
                await HandleMessageAsync(messageJson);
            }
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("[Client] Listening cancelled");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[Client] Error in message listener: {ex.Message}");
        }
    }
    
    private async Task HandleMessageAsync(string messageJson)
    {
        try
        {
            using var document = JsonDocument.Parse(messageJson);
            var root = document.RootElement;
            
            if (!root.TryGetProperty("type", out var typeElement))
            {
                Console.WriteLine("[Client] Received message without type field");
                return;
            }
            
            var messageType = typeElement.GetString();
            
            switch (messageType)
            {
                case "save_state":
                    await HandleSaveStateAsync(root);
                    break;
                    
                case "recommendations_response":
                    HandleRecommendationsResponse(root);
                    break;
                    
                default:
                    Console.WriteLine($"[Client] Received unknown message type: {messageType}");
                    break;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[Client] Error handling message: {ex.Message}");
        }
    }
    
    private async Task HandleSaveStateAsync(JsonElement root)
    {
        if (root.TryGetProperty("data", out var dataElement))
        {
            var stateData = JsonSerializer.Deserialize<StateData>(dataElement.GetRawText());
            Console.WriteLine($"[Client] Server requested state save: {dataElement.GetRawText()}");
            
            // Invoke the event handler (your C# backend would persist this)
            OnSaveStateRequested?.Invoke(this, stateData);
            
            // Example: Save to database
            Console.WriteLine($"[Client] Would save to database: {JsonSerializer.Serialize(stateData, new JsonSerializerOptions { WriteIndented = true })}");
        }
        
        await Task.CompletedTask;
    }
    
    private void HandleRecommendationsResponse(JsonElement root)
    {
        if (root.TryGetProperty("request_id", out var requestIdElement) &&
            root.TryGetProperty("data", out var dataElement))
        {
            var requestId = requestIdElement.GetString();
            
            if (_pendingRequests.TryRemove(requestId, out var tcs))
            {
                tcs.SetResult(dataElement);
                Console.WriteLine($"[Client] Received recommendations response");
            }
        }
    }
    
    public async Task SendAnalyticEventAsync(object eventData)
    {
        var message = new
        {
            type = "analytic_event",
            data = eventData
        };
        
        await SendMessageAsync(message);
        Console.WriteLine($"[Client] Sent analytic event");
    }
    
    public async Task<RecommendationsResponse> GetRecommendationsAsync(string userId, TimeSpan? timeout = null)
    {
        var requestId = Guid.NewGuid().ToString();
        var tcs = new TaskCompletionSource<JsonElement>();
        _pendingRequests[requestId] = tcs;
        
        var message = new
        {
            type = "get_recommendations",
            request_id = requestId,
            data = new { user_id = userId }
        };
        
        await SendMessageAsync(message);
        Console.WriteLine($"[Client] Sent get_recommendations for user {userId}");
        
        try
        {
            // Wait for response with timeout
            var timeoutDuration = timeout ?? TimeSpan.FromSeconds(5);
            var resultTask = tcs.Task;
            
            if (await Task.WhenAny(resultTask, Task.Delay(timeoutDuration)) == resultTask)
            {
                var result = await resultTask;
                var response = JsonSerializer.Deserialize<RecommendationsResponse>(result.GetRawText());
                Console.WriteLine($"[Client] Received recommendations: {string.Join(", ", response.Recommendations)}");
                return response;
            }
            else
            {
                throw new TimeoutException($"Request {requestId} timed out after {timeoutDuration.TotalSeconds}s");
            }
        }
        finally
        {
            _pendingRequests.TryRemove(requestId, out _);
        }
    }
    
    private async Task SendMessageAsync(object message)
    {
        var json = JsonSerializer.Serialize(message);
        var bytes = Encoding.UTF8.GetBytes(json);
        
        await _webSocket.SendAsync(
            new ArraySegment<byte>(bytes),
            WebSocketMessageType.Text,
            endOfMessage: true,
            _cancellationTokenSource.Token);
    }
    
    public async Task CloseAsync()
    {
        if (_webSocket.State == WebSocketState.Open)
        {
            await _webSocket.CloseAsync(
                WebSocketCloseStatus.NormalClosure,
                "Client closing",
                CancellationToken.None);
        }
        Console.WriteLine("[Client] Connection closed");
    }
    
    public void Dispose()
    {
        _cancellationTokenSource?.Cancel();
        _webSocket?.Dispose();
        _cancellationTokenSource?.Dispose();
    }
}

// Data models
public class StateData
{
    public int AnalyticsCount { get; set; }
    public Dictionary<string, string> UserPreferences { get; set; }
}

public class RecommendationsResponse
{
    public string UserId { get; set; }
    public List<string> Recommendations { get; set; }
}
