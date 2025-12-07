FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files first
COPY proto/ /app/proto/

# Generate gRPC code from proto files
RUN python -m grpc_tools.protoc \
    -I=/app/proto \
    --python_out=/app \
    --grpc_python_out=/app \
    /app/proto/carbon_service.proto

# Copy the rest of the application
COPY . /app/

# Create output directory for Pathway streaming results
RUN mkdir -p /app/output

CMD ["python", "grpc_server.py"]
