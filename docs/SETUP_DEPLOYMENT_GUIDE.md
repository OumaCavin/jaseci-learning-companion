# 🚀 Complete Setup & Deployment Guide

**Author**: Cavin Otieno  
**Contact**: [cavin.otieno012@gmail.com](mailto:cavin.otieno012@gmail.com) | +254708101604  
**LinkedIn**: [Cavin Otieno](https://www.linkedin.com/in/cavin-otieno-9a841260/)  
**WhatsApp**: [wa.me/+254708101604](wa.me/+254708101604)

---

## 📋 **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Development Environment Setup](#development-environment-setup)
3. [Local Development Quick Start](#local-development-quick-start)
4. [Docker Development Setup](#docker-development-setup)
5. [Kubernetes Production Deployment](#kubernetes-production-deployment)
6. [Database Setup & Migration](#database-setup--migration)
7. [Security Configuration](#security-configuration)
8. [Monitoring & Observability](#monitoring--observability)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## 🔧 **Prerequisites**

### **System Requirements**

#### **Minimum Development Environment**
- **OS**: Linux (Ubuntu 20.04+), macOS (Big Sur+), Windows 10+ (WSL2)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB available space
- **Network**: Stable internet connection

#### **Required Software**

```bash
# Core Development Tools
Docker 24.0+ & Docker Compose 2.0+
Node.js 18+ & npm/yarn/pnpm
Python 3.11+ & pip/poetry
Git 2.40+

# Database Systems
PostgreSQL 15+
Redis 7+
Neo4j 5.0+
Elasticsearch 8.0+

# Kubernetes (Production)
kubectl 1.28+
helm 3.11+
```

#### **Installation Commands**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose nodejs npm python3 python3-pip git

# macOS
brew install docker docker-compose node python git

# Python Environment
pip install poetry

# Kubernetes Tools
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
sudo apt-get install helm

# Verify installations
docker --version
node --version
python3 --version
kubectl version --client
helm version
```

---

## 🛠️ **Development Environment Setup**

### **1. Clone Repository**

```bash
git clone https://github.com/OumaCavin/jaseci-learning-companion.git
cd jaseci-learning-companion
git config user.name "OumaCavin"
git config user.email "cavin.otieno012@gmail.com"
```

### **2. Environment Configuration**

```bash
# Create environment files
cp .env.example .env
cp .env.example .env.local

# Edit configuration
nano .env
```

#### **Core Configuration (.env)**

```bash
# Application Environment
JASECI_ENV=development
APP_NAME=Jaseci Learning Companion
APP_VERSION=2.0.0-enterprise

# Database Configuration
DATABASE_URL=postgresql://jaseci_user:secure_password@localhost:5432/jaseci_learning
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=jaseci_learning
POSTGRES_USER=jaseci_user
POSTGRES_PASSWORD=secure_password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Neo4j Configuration (for OSP Graphs)
NEO4J_URI=bolt://localhost:7687
NEO4J_HOST=localhost
NEO4J_PORT=7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_secure_password

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Security Configuration
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ENCRYPTION_KEY=your-encryption-key-for-sensitive-data

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=cavin.otieno012@gmail.com
SMTP_PASSWORD=oakjazoekos
EMAIL_FROM=Jaseci Learning Companion <cavin.otieno012@gmail.com>

# External API Keys
OPENAI_API_KEY=your-openai-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
JAEGER_PORT=14268

# Feature Flags
ENABLE_REALTIME_UPDATES=true
ENABLE_CCG_ANALYSIS=true
ENABLE_OSP_GRAPHS=true
ENABLE_QUALITY_ASSESSMENT=true
ENABLE_ADVANCED_METRICS=true
ENABLE_SECURITY_SCANNING=true

# Agent Configuration
MAX_CONCURRENT_AGENTS=50
AGENT_HEARTBEAT_INTERVAL=30
ORCHESTRATION_TIMEOUT=300
AGENT_REGISTRY_TIMEOUT=60

# File Upload Configuration
MAX_FILE_SIZE=10MB
UPLOAD_PATH=uploads/
ALLOWED_EXTENSIONS=.jas,.py,.js,.ts,.json,.md
```

### **3. Database Setup**

#### **PostgreSQL Setup**

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE jaseci_learning;
CREATE USER jaseci_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE jaseci_learning TO jaseci_user;
\q
```

#### **Redis Setup**

```bash
# Install Redis
sudo apt install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis connection
redis-cli ping
# Should return: PONG
```

#### **Neo4j Setup (for OSP Graphs)**

```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 5.0' | sudo tee -a /etc/apt/sources.list.d/neo4j.list

# Install Neo4j
sudo apt update
sudo apt install neo4j

# Configure Neo4j
sudo neo4j-admin set-initial-password neo4j_secure_password

# Start Neo4j
sudo systemctl start neo4j
sudo systemctl enable neo4j

# Access Neo4j Browser
# http://localhost:7474
# Username: neo4j
# Password: neo4j_secure_password
```

#### **Elasticsearch Setup**

```bash
# Install Elasticsearch
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-8.x.list
sudo apt update
sudo apt install elasticsearch

# Configure Elasticsearch
sudo nano /etc/elasticsearch/elasticsearch.yml

# Start Elasticsearch
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
```

---

## 💻 **Local Development Quick Start**

### **1. Backend Setup (Python)**

```bash
# API Gateway
cd services/core/api_gateway
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# New Terminal: Multi-Agent Orchestrator
cd services/orchestrator
python -m venv venv_orch
source venv_orch/bin/activate
pip install -r requirements.txt
python -m orchestrator.main

# New Terminal: Individual Agents
cd services/orchestrator/agents/learning_progress
python -m learning_progress_agent

# New Terminal: OSP Graph Service (NEW)
cd services/core/osp_graph_service
python -m venv venv_osp
source venv_osp/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### **2. Frontend Setup (React)**

```bash
# Frontend Dashboard
cd frontend/web-dashboard
npm install

# Start development server
npm run dev

# Access application
# http://localhost:3000
```

### **3. Database Migration**

```bash
# Run database migrations
cd services/core/api_gateway
source venv/bin/activate
python -m alembic upgrade head

# Seed initial data (optional)
python -m scripts.seed_data
```

### **4. Verify Installation**

```bash
# Test API endpoints
curl http://localhost:8000/health

# Test WebSocket connection
wscat ws://localhost:8000/ws

# Test Neo4j connection (OSP service)
curl http://localhost:8001/health

# Test frontend
curl http://localhost:3000
```

---

## 🐳 **Docker Development Setup**

### **1. Docker Compose Development**

```bash
# Start development stack
docker-compose -f infrastructure/docker/dev/docker-compose.yml up -d

# Check running services
docker-compose -f infrastructure/docker/dev/docker-compose.yml ps

# View logs
docker-compose -f infrastructure/docker/dev/docker-compose.yml logs -f

# Stop services
docker-compose -f infrastructure/docker/dev/docker-compose.yml down
```

### **2. Docker Compose Configuration**

#### **Development Docker Compose** (`infrastructure/docker/dev/docker-compose.yml`)

```yaml
version: '3.8'

services:
  # Database Services
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: jaseci_learning
      POSTGRES_USER: jaseci_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../../database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U jaseci_user -d jaseci_learning"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  neo4j:
    image: neo4j:5.0
    environment:
      NEO4J_AUTH: neo4j/neo4j_secure_password
      NEO4J_dbms_memory_heap_initial__size: 512m
      NEO4J_dbms_memory_heap_max__size: 1G
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "neo4j_secure_password", "RETURN 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  elasticsearch:
    image: elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Backend Services
  api-gateway:
    build:
      context: ../../services/core/api_gateway
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://jaseci_user:secure_password@postgres:5432/jaseci_learning
      - REDIS_URL=redis://redis:6379/0
      - NEO4J_URI=bolt://neo4j:7687
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    volumes:
      - ../../services/core/api_gateway:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  orchestrator:
    build:
      context: ../../services/orchestrator
      dockerfile: Dockerfile.dev
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://jaseci_user:secure_password@postgres:5432/jaseci_learning
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ../../services/orchestrator:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python -m orchestrator.main

  osp-graph-service:
    build:
      context: ../../services/core/osp_graph_service
      dockerfile: Dockerfile.dev
    ports:
      - "8001:8001"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=neo4j_secure_password
    volumes:
      - ../../services/core/osp_graph_service:/app
    depends_on:
      neo4j:
        condition: service_healthy
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8001

  # Frontend Service
  frontend:
    build:
      context: ../../frontend/web-dashboard
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    volumes:
      - ../../frontend/web-dashboard:/app
      - /app/node_modules
    depends_on:
      - api-gateway
    command: npm run dev

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
  neo4j_logs:
  elasticsearch_data:

networks:
  default:
    name: jaseci_learning_dev
```

---

## ☸️ **Kubernetes Production Deployment**

### **1. Prerequisites for Production**

```bash
# Kubernetes cluster access
kubectl cluster-info

# Helm repository setup
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add neo4j https://helm.neo4j.com/neo4j
helm repo update

# Create namespace
kubectl create namespace jaseci-learning-prod
```

### **2. Secret Management**

```bash
# Create production secrets
kubectl create secret generic jaseci-secrets \
  --from-env-file=.env.production \
  --namespace=jaseci-learning-prod

# Create SSL certificates (for HTTPS)
kubectl create secret tls jaseci-tls \
  --cert=tls.crt \
  --key=tls.key \
  --namespace=jaseci-learning-prod
```

### **3. Database Deployment**

#### **PostgreSQL on Kubernetes**

```yaml
# infrastructure/kubernetes/prod/postgres.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: jaseci-learning-prod
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: jaseci-learning-prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: jaseci_learning
        - name: POSTGRES_USER
          value: jaseci_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: jaseci-secrets
              key: POSTGRES_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: jaseci-learning-prod
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

#### **Neo4j on Kubernetes**

```yaml
# infrastructure/kubernetes/prod/neo4j.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: neo4j-pvc
  namespace: jaseci-learning-prod
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neo4j
  namespace: jaseci-learning-prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.0
        env:
        - name: NEO4J_AUTH
          valueFrom:
            secretKeyRef:
              name: jaseci-secrets
              key: NEO4J_AUTH
        - name: NEO4J_dbms_memory_heap_initial__size
          value: "1g"
        - name: NEO4J_dbms_memory_heap_max__size
          value: "2g"
        ports:
        - containerPort: 7474
        - containerPort: 7687
        volumeMounts:
        - name: neo4j-storage
          mountPath: /data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: neo4j-storage
        persistentVolumeClaim:
          claimName: neo4j-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
  namespace: jaseci-learning-prod
spec:
  selector:
    app: neo4j
  ports:
  - port: 7687
    targetPort: 7687
    name: bolt
  - port: 7474
    targetPort: 7474
    name: http
  type: ClusterIP
```

### **4. Application Deployment**

#### **API Gateway Deployment**

```yaml
# infrastructure/kubernetes/prod/api-gateway.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-gateway-config
  namespace: jaseci-learning-prod
data:
  DATABASE_URL: "postgresql://jaseci_user:$(POSTGRES_PASSWORD)@postgres:5432/jaseci_learning"
  REDIS_URL: "redis://redis:6379/0"
  ELASTICSEARCH_URL: "http://elasticsearch:9200"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: jaseci-learning-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: jaseci-learning/api-gateway:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: jaseci-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: jaseci-secrets
              key: JWT_SECRET_KEY
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: jaseci-learning-prod
spec:
  selector:
    app: api-gateway
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

#### **OSP Graph Service Deployment**

```yaml
# infrastructure/kubernetes/prod/osp-graph-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: osp-graph-service
  namespace: jaseci-learning-prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: osp-graph-service
  template:
    metadata:
      labels:
        app: osp-graph-service
    spec:
      containers:
      - name: osp-graph-service
        image: jaseci-learning/osp-graph-service:latest
        env:
        - name: NEO4J_URI
          value: "bolt://neo4j:7687"
        - name: NEO4J_USER
          valueFrom:
            secretKeyRef:
              name: jaseci-secrets
              key: NEO4J_USER
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: jaseci-secrets
              key: NEO4J_PASSWORD
        ports:
        - containerPort: 8001
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: osp-graph-service
  namespace: jaseci-learning-prod
spec:
  selector:
    app: osp-graph-service
  ports:
  - port: 80
    targetPort: 8001
  type: ClusterIP
```

### **5. Horizontal Pod Autoscaling**

```yaml
# infrastructure/kubernetes/prod/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: jaseci-learning-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: osp-graph-service-hpa
  namespace: jaseci-learning-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: osp-graph-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### **6. Ingress Configuration**

```yaml
# infrastructure/kubernetes/prod/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jaseci-learning-ingress
  namespace: jaseci-learning-prod
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - jaseci-learning.com
    secretName: jaseci-tls
  rules:
  - host: jaseci-learning.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 80
      - path: /osp
        pathType: Prefix
        backend:
          service:
            name: osp-graph-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

### **7. Deploy to Production**

```bash
# Deploy all services
kubectl apply -f infrastructure/kubernetes/prod/

# Check deployment status
kubectl get all -n jaseci-learning-prod

# Check logs
kubectl logs -f deployment/api-gateway -n jaseci-learning-prod
kubectl logs -f deployment/osp-graph-service -n jaseci-learning-prod

# Scale services
kubectl scale deployment api-gateway --replicas=5 -n jaseci-learning-prod

# Check HPA
kubectl get hpa -n jaseci-learning-prod

# Port forward for testing
kubectl port-forward svc/api-gateway 8000:80 -n jaseci-learning-prod
kubectl port-forward svc/osp-graph-service 8001:80 -n jaseci-learning-prod

# Access application
# https://jaseci-learning.com
```

---

## 📊 **Database Setup & Migration**

### **1. Database Schema Setup**

```bash
# Apply database migrations
cd services/core/api_gateway
source venv/bin/activate
python -m alembic upgrade head

# Verify database connection
python -c "from database.connection import get_db; print('Database connected successfully')"
```

### **2. Neo4j Schema Setup (OSP Graphs)**

```bash
# Run Neo4j schema initialization
cd services/core/osp_graph_service
source venv/bin/activate
python -m database.neo4j_client --init-schema

# Verify Neo4j connection
python -c "from database.neo4j_client import Neo4jClient; print('Neo4j connected successfully')"
```

### **3. Seed Initial Data**

```bash
# Create admin user
python -m scripts.create_admin_user \
  --email admin@jaseci-learning.com \
  --password secure_admin_password \
  --role admin

# Load sample Jaseci code for OSP testing
python -m scripts.load_sample_code

# Create default learning paths
python -m scripts.create_default_paths
```

---

## 🔒 **Security Configuration**

### **1. SSL/TLS Setup**

```bash
# Generate SSL certificates (self-signed for development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key \
  -out tls.crt \
  -subj "/C=KE/ST=Nairobi/L=Nairobi/O=Jaseci Learning/OU=IT/CN=jaseci-learning.local"

# For production, use Let's Encrypt or commercial certificates
certbot certonly --webroot -w /var/www/jaseci-learning -d jaseci-learning.com
```

### **2. JWT Configuration**

```python
# JWT Configuration (backend/config/jwt.py)
import os
from datetime import timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

class JWTConfig:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secure-secret-key")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_HOURS", 24)) * 60
    
    @classmethod
    def create_access_token(cls, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt
    
    @classmethod
    def verify_token(cls, token: str):
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except JWTError:
            return None
```

### **3. Rate Limiting**

```python
# API Gateway Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/analyze")
@limiter.limit("10/minute")
async def analyze_code(request: Request, code: str):
    # Code analysis logic
    pass
```

---

## 📈 **Monitoring & Observability**

### **1. Prometheus Configuration**

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "jaseci_learning_rules.yml"

scrape_configs:
  - job_name: 'jaseci-api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: /metrics
    
  - job_name: 'jaseci-osp-service'
    static_configs:
      - targets: ['osp-graph-service:8001']
    metrics_path: /metrics
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
      
  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:7474']
```

### **2. Grafana Dashboards**

```bash
# Install Grafana
helm install grafana prometheus-community/grafana \
  --set adminPassword=admin_password \
  --namespace=jaseci-learning-prod

# Import dashboards
kubectl apply -f monitoring/grafana-dashboards/
```

### **3. Jaeger Tracing**

```bash
# Deploy Jaeger
helm install jaeger jaegertracing/jaeger \
  --namespace=jaseci-learning-prod

# Configure tracing in applications
JAEGER_ENDPOINT=http://jaeger-collector:14268/api/traces
```

---

## ⚡ **Performance Optimization**

### **1. Database Optimization**

```sql
-- PostgreSQL indexes
CREATE INDEX CONCURRENTLY idx_learning_progress_user_id ON learning_progress(user_id);
CREATE INDEX CONCURRENTLY idx_code_analysis_timestamp ON code_analysis(created_at);
CREATE INDEX CONCURRENTLY idx_osp_nodes_project_id ON osp_nodes(project_id);

-- Neo4j indexes for OSP graphs
CREATE INDEX osp_project_id IF NOT EXISTS FOR (n:OSPNode) ON (n.project_id);
CREATE INDEX osp_node_type IF NOT EXISTS FOR (n:OSPNode) ON (n.node_type);
```

### **2. Redis Caching Strategy**

```python
# Redis caching implementation
import redis
import json
from typing import Any, Optional

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
    
    async def get_cache(self, key: str) -> Optional[Any]:
        cached_data = self.redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def set_cache(self, key: str, value: Any, expire: int = 3600):
        self.redis_client.setex(
            key, 
            expire, 
            json.dumps(value, default=str)
        )
```

### **3. Connection Pooling**

```python
# Database connection pooling
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

---

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

#### **1. Database Connection Issues**

```bash
# Check PostgreSQL status
sudo systemctl status postgresql
sudo systemctl restart postgresql

# Test PostgreSQL connection
psql -h localhost -U jaseci_user -d jaseci_learning

# Check Neo4j status
sudo systemctl status neo4j
sudo systemctl restart neo4j

# Test Neo4j connection
cypher-shell -u neo4j -p neo4j_secure_password
```

#### **2. Redis Connection Issues**

```bash
# Check Redis status
sudo systemctl status redis-server
sudo systemctl restart redis-server

# Test Redis connection
redis-cli ping
redis-cli monitor
```

#### **3. Application Issues**

```bash
# Check application logs
kubectl logs -f deployment/api-gateway -n jaseci-learning-prod

# Check resource usage
kubectl top pods -n jaseci-learning-prod

# Check network connectivity
kubectl exec -it <pod-name> -- /bin/bash
curl -v http://api-gateway:80/health
```

#### **4. Frontend Build Issues**

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version compatibility
node --version
npm --version
```

### **Performance Issues**

```bash
# Check system resources
free -h
df -h
top

# Check database performance
psql -d jaseci_learning -c "SELECT * FROM pg_stat_activity;"

# Check Redis memory usage
redis-cli info memory
redis-cli info stats

# Check Neo4j performance
cypher-shell -u neo4j -p neo4j_secure_password "CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition;"
```

---

## 📞 **Support & Maintenance**

### **Contact Information**

- **📧 Email**: [cavin.otieno012@gmail.com](mailto:cavin.otieno012@gmail.com)
- **📱 WhatsApp**: [+254708101604](wa.me/+254708101604)
- **💼 LinkedIn**: [Cavin Otieno](https://www.linkedin.com/in/cavin-otieno-9a841260/)
- **🐛 Issues**: [GitHub Issues](https://github.com/OumaCavin/jaseci-learning-companion/issues)

### **Maintenance Tasks**

```bash
# Daily backups
./scripts/backup_database.sh

# Log rotation
./scripts/rotate_logs.sh

# Security updates
./scripts/security_updates.sh

# Performance monitoring
./scripts/performance_check.sh
```

### **Emergency Procedures**

```bash
# Emergency database restore
./scripts/restore_database.sh backup_YYYY-MM-DD.sql

# Scale down during incident
kubectl scale deployment api-gateway --replicas=1 -n jaseci-learning-prod

# Emergency contact
# Call +254708101604
```

---

**🚀 Built with ❤️ by Cavin Otieno**  
*Your comprehensive guide to enterprise-grade deployment*

> **"From development to production - we've got you covered!"** - Cavin Otieno

---

*For additional support, documentation, and community resources, visit our [GitHub repository](https://github.com/OumaCavin/jaseci-learning-companion) or contact our support team.*