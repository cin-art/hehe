# docker-compose.yml
version: '3.8'

services:
  # Frontend Web Application
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://api:8000
      - REACT_APP_WEBSOCKET_URL=ws://websocket:8001
    depends_on:
      - api
      - websocket

  # Main API Service
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/knowledgedb
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=your-secret-key
      - STRIPE_API_KEY=${STRIPE_API_KEY}
    depends_on:
      - db
      - redis

  # WebSocket Service for Real-time Collaboration
  websocket:
    build: ./websocket
    ports:
      - "8001:8001"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  # Database
  db:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=knowledgedb
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis for Caching and Real-time Features
  redis:
    image: redis:6
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Elasticsearch for Search
  elasticsearch:
    image: elasticsearch:7.17.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  # Object Storage
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=password123
    volumes:
      - minio_data:/data
    command: server --console-address ":9001" /data

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
  minio_data:

# Kubernetes deployment for production
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledge-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: knowledge-platform
  template:
    metadata:
      labels:
        app: knowledge-platform
    spec:
      containers:
      - name: api
        image: knowledge-platform/api:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: database-url
