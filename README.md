# origin
Prototype recommender code for ORIGIN project

# websocket mockup

pip install fastapi uvicorn websockets

Run the server:

python server.py

Run the client in another terminal:

python client.py

# gRPC mockup

python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. contract.proto

Run the server:

python server.py

Run the client in another terminal:

python client.py
