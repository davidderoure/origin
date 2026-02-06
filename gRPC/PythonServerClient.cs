// PythonServerClient.cs
using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using Grpc.Net.Client;
using Pythonserver;

public class PythonServerClient : IDisposable
{
    private readonly GrpcChannel _channel;
    private readonly EventService.EventServiceClient _client;
    private AsyncDuplexStreamingCall<ClientMessage, ServerMessage> _stream;
    private readonly ConcurrentDictionary<string, TaskCompletionSource<RecommendationsResponse>> _pendingRequests;
    private readonly CancellationTokenSource _cancellationTokenSource;
    
    public event EventHandler<SaveStateRequest> OnSaveStateRequested;
    
    public PythonServerClient(string address = "http://localhost:50051")
    {
        _channel = GrpcChannel.ForAddress(address);
        _client = new EventService.EventServiceClient(_channel);
        _pendingRequests = new ConcurrentDictionary<string, TaskCompletionSource<RecommendationsResponse>>();
        _cancellationTokenSource = new CancellationTokenSource();
    }
    
    public async Task ConnectAsync()
    {
        _stream = _client.EventStream(cancellationToken: _cancellationTokenSource.Token);
        Console.WriteLine("[Client] Connected to server");
        
        // Start listening for server messages
        _ = Task.Run(ListenForServerMessagesAsync);
    }
    
    private async Task ListenForServerMessagesAsync()
    {
        try
        {
            await foreach (var serverMsg in _stream.ResponseStream.ReadAllAsync(_cancellationTokenSource.Token))
            {
                switch (serverMsg.MessageTypeCase)
                {
                    case ServerMessage.MessageTypeOneofCase.RecommendationsResponse:
                        HandleRecommendationsResponse(serverMsg.RecommendationsResponse);
                        break;
                        
                    case ServerMessage.MessageTypeOneofCase.SaveState:
                        HandleSaveState(serverMsg.SaveState);
                        break;
                }
            }
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("[Client] Listening cancelled");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[Client] Error: {ex.Message}");
        }
    }
    
    private void HandleRecommendationsResponse(RecommendationsResponse response)
    {
        if (_pendingRequests.TryRemove(response.RequestId, out var tcs))
        {
            tcs.SetResult(response);
            Console.WriteLine($"[Client] Received recommendations for {response.UserId}");
        }
    }
    
    private void HandleSaveState(SaveStateRequest saveState)
    {
        Console.WriteLine($"[Client] Server requested state save");
        OnSaveStateRequested?.Invoke(this, saveState);
    }
    
    public async Task SendAnalyticEventAsync(string action, string target)
    {
        var message = new ClientMessage
        {
            AnalyticEvent = new AnalyticEvent
            {
                Action = action,
                Target = target
            }
        };
        
        await _stream.RequestStream.WriteAsync(message);
        Console.WriteLine($"[Client] Sent analytic event: {action} on {target}");
    }
    
    public async Task<RecommendationsResponse> GetRecommendationsAsync(string userId)
    {
        var requestId = Guid.NewGuid().ToString();
        var tcs = new TaskCompletionSource<RecommendationsResponse>();
        _pendingRequests[requestId] = tcs;
        
        var message = new ClientMessage
        {
            GetRecommendations = new GetRecommendationsRequest
            {
                RequestId = requestId,
                UserId = userId
            }
        };
        
        await _stream.RequestStream.WriteAsync(message);
        Console.WriteLine($"[Client] Sent get_recommendations for {userId}");
        
        try
        {
            return await tcs.Task.WaitAsync(TimeSpan.FromSeconds(5));
        }
        finally
        {
            _pendingRequests.TryRemove(requestId, out _);
        }
    }
    
    public async Task CloseAsync()
    {
        await _stream.RequestStream.CompleteAsync();
        _cancellationTokenSource.Cancel();
        Console.WriteLine("[Client] Connection closed");
    }
    
    public void Dispose()
    {
        _cancellationTokenSource?.Dispose();
        _channel?.Dispose();
    }
}
