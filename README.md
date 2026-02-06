# origin
Prototype recommender code for ORIGIN project

# websocket mockup

pip install fastapi uvicorn websockets

Run the server:

python server.py

Run the client in another terminal:

python client.py

# gRPC mockup

pip install grpcio 
pip install grpcio-tools

python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. contract.proto

This creates contract_pb2.py and contract_pb2_grpc.py

Run the server:

python server.py

Run the client in another terminal:

python client.py
