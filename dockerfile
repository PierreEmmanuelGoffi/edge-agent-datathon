FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    sqlite3 \
    libsqlite3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Clone repository
RUN git clone https://github.com/PierreEmmanuelGoffi/edge-agent-datathon.git .

# Upgrade pip
RUN pip3 install --upgrade pip

# Install Python dependencies
RUN pip3 install -r requirements.txt -v

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Add an entrypoint script to handle environment variables
COPY <<'EOF' /app/docker-entrypoint.sh
#!/bin/bash
set -e

# List of required environment variables
required_vars=(
    "SERPER_API_KEY"
    "OPENAI_API_KEY"
    "GROQ_API_KEY"
    "AWS_REGION"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "AWS_S3_BUCKET_NAME"
)

# Check for required environment variables
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var environment variable is required"
        exit 1
    fi
done

# Create .env file from environment variables
echo "SERPER_API_KEY=$SERPER_API_KEY" > .env
echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env
echo "GROQ_API_KEY=$GROQ_API_KEY" >> .env
echo "AWS_REGION=$AWS_REGION" >> .env
echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" >> .env
echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> .env
echo "AWS_S3_BUCKET_NAME=$AWS_S3_BUCKET_NAME" >> .env

# Start the Streamlit app
exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0
EOF

RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]