# origin
Prototype recommender code for ORIGIN project

## Demo

The recommender logic is in rec2.py

The demo creates a web server which calls the recommender code. It includes
25 AI-generated stories for demo and test purposes.

pip install flask

python app.py

Open your browser to: http://localhost:5000

# Experiments in IPC

This is very simple client-server code using different IPC methods, in order
to make a preliminary assessment of what would be best for the backend integration
of the python code to be called by C# and potentially to call C#

## Web server for prototyping

pip install fastapi uvicorn

Run the server:

python server_web.py

3. Open browser:

http://localhost:8000

## websocket mockup

pip install fastapi uvicorn websockets

Run the server:

python server.py

Run the client in another terminal:

python client.py

## gRPC mockup

pip install grpcio 
pip install grpcio-tools

python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. contract.proto

This creates contract_pb2.py and contract_pb2_grpc.py

Run the server:

python server.py

Run the client in another terminal:

python client.py

## named pipes and sockets

python server_socket.py

Run the client in another terminal:

python client_socket.py
