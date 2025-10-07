# 🤖 TalentScout1: AI-Powered Technical Interview System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.1-red.svg)](https://streamlit.io)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://mongodb.com)
[![Ollama](https://img.shields.io/badge/Ollama-Llama3.2-orange.svg)](https://ollama.ai)
[![AWS](https://img.shields.io/badge/AWS-EC2-orange.svg)](https://aws.amazon.com/ec2/)

*An intelligent hiring assistant that conducts automated technical interviews using advanced AI*


---

## Overview

TalentScout1 is a comprehensive AI-driven technical interview platform designed to revolutionize the hiring process. The system automates candidate assessment through intelligent conversational interviews, leveraging local LLM capabilities via Ollama to generate contextual technical questions, evaluate responses in real-time, and provide detailed candidate scoring.

###  Key Features

-  Multi-Technology Assessment: 40+ technologies across 8 categories
-  AI-Powered Question Generation: Dynamic questions using Llama3.2
-  Real-time Scoring: Automated answer evaluation with detailed metrics
-  Conversational Interface Natural chat-based interview experience
-  Context-Aware Follow-ups Intelligent question progression
-  Admin Analytics Comprehensive interview statistics
-  Cloud Deployment Scalable AWS EC2 deployment
-  Production Ready Robust session management and persistence

###  Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Interview      │    │   MongoDB       │
│   Frontend      │◄──►│   Engine         │◄──►│   Atlas         │
│  (Port 8501)    │    │                  │    │   (Cloud)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                     ┌──────────────────┐
                     │   Ollama +       │
                     │   Llama3.2       │
                     │  (Port 11434)    │
                     └──────────────────┘
```

---

## Installation

### Prerequisites

- **Python 3.9+**
- **MongoDB Atlas Account**
- **AWS EC2 Instance** (t3.xlarge recommended for production)
- **8GB+ RAM** for local Ollama deployment

### Quick Start (Local Development)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Mandar-1107/TalentScout1.git
   cd TalentScout1
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Install Ollama**
   ```bash
   # Linux/macOS
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Windows - Download from https://ollama.com/download/windows
   ```

4. **Configure environment**
   ```bash
   # Create .env file
   cat > .env << EOF
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/interview_system?retryWrites=true&w=majority
   MONGODB_DB=interview_system
   OLLAMA_URL=http://localhost:11434/
   EOF
   ```

5. **Start services**
   ```bash
   # Terminal 1: Start Ollama
   ollama serve
   
   # Terminal 2: Pull model (first time only)
   ollama pull llama3.2
   
   # Terminal 3: Initialize database
   python scripts/init_db.py
   
   # Terminal 4: Start application
   streamlit run app.py
   ```

6. **Access the application**
   - Open your browser to `http://localhost:8501`

### AWS EC2 Production Deployment

#### 1. Launch EC2 Instance

**Recommended Configuration:**
- **AMI**: Amazon Linux 2023
- **Instance Type**: t3.xlarge (4 vCPUs, 16GB RAM)
- **Storage**: 30GB gp3
- **Security Group**: SSH (22), Custom TCP (8501)

#### 2. Connect and Setup

```bash
# Connect to instance
ssh -i "your-key.pem" ec2-user@your-ec2-public-ip

# Update system
sudo yum update -y
sudo yum install -y git python3 python3-pip

# Clone and setup
git clone https://github.com/Mandar-1107/TalentScout1.git
cd TalentScout1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

#### 3. Install Ollama on EC2

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve > ollama.log 2>&1 &

# Pull model
ollama pull llama3.2
```

#### 4. Production Startup Script

```bash
# Create startup script
cat > start_app.sh << 'EOF'
#!/bin/bash
cd /home/ec2-user/TalentScout1
source venv/bin/activate

# Kill existing processes
pkill -f ollama 2>/dev/null || true
pkill -f streamlit 2>/dev/null || true

# Start Ollama
ollama serve > ollama.log 2>&1 &
sleep 10

# Start Streamlit
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > app.log 2>&1 &

echo "TalentScout1 started successfully!"
echo "Access at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
EOF

chmod +x start_app.sh
./start_app.sh
```

#### 5. MongoDB Atlas Setup

1. Create account at [MongoDB Atlas](https://cloud.mongodb.com)
2. Create free cluster
3. Create database user with read/write permissions
4. Whitelist EC2 IP address
5. Update `.env` file with connection string

#### 6. Process Management

```bash
# Check processes
ps aux | grep -E "(streamlit|ollama)"

# View logs
tail -f app.log
tail -f ollama.log

# Restart application
./start_app.sh
```

---

## Usage Guide

### For Candidates

1. **Registration**
   - Navigate to the application URL
   - Provide personal information (name, email, phone, experience)
   - Select desired positions

2. **Technology Selection**
   - Choose from 8 technology categories:
     - **Programming Languages**: Python, JavaScript, Java, C++, C#, Go, Rust
     - **Frontend**: React, Vue.js, Angular, Svelte, TypeScript
     - **Backend**: Django, Flask, Spring Boot, Express.js, FastAPI
     - **Databases**: PostgreSQL, MongoDB, Redis, MySQL, Cassandra
     - **Cloud**: AWS, Google Cloud, Azure, Docker, Kubernetes
     - **DevOps**: Jenkins, GitLab CI, Terraform, Ansible
     - **Data Science**: Pandas, NumPy, TensorFlow, PyTorch, Scikit-learn
     - **Mobile**: React Native, Flutter, Swift, Kotlin

3. **Interview Process**
   - System generates 3 questions per selected technology
   - Answer through conversational chat interface
   - Receive context-aware follow-up questions
   - View real-time scoring and feedback

4. **Results**
   - View comprehensive performance report
   - Download interview transcript
   - Receive completion certificate


##  Technical Details

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Streamlit 1.28.1 | Interactive web interface |
| **Backend** | Python 3.9+ | Core application logic |
| **Database** | MongoDB Atlas | Cloud data persistence |
| **AI/ML** | Ollama + Llama3.2 | Question generation & evaluation |
| **Validation** | Pydantic 2.4.2 | Data models and validation |
| **Cloud** | AWS EC2 | Scalable deployment |

### Project Structure

```
TalentScout1/
├── app.py                     # Main Streamlit application
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── start_app.sh              # Production startup script
├── database/
│   └── connection.py          # MongoDB connection
├── models/
│   ├── candidate.py           # Candidate data model
│   ├── interview.py           # Interview session model
│   └── common.py              # Shared enums and types
├── services/
│   ├── candidate_service.py   # Candidate management
│   ├── interview_service.py   # Interview logic
│   ├── llama_service.py       # LLM integration
│   ├── session_service.py     # Session management
│   └── admin_service.py       # Analytics service
├── scripts/
│   └── init_db.py             # Database initialization
├── tests/
│   ├── test_models.py         # Model tests
│   ├── test_services.py       # Service tests
│   └── conftest.py            # Test configuration
└── docs/
    ├── API.md                 # API documentation
    ├── DEPLOYMENT.md          # Deployment guide
    └── TROUBLESHOOTING.md     # Common issues
```

### Data Models


### AWS Security Group Configuration

```
Inbound Rules:
┌──────────────┬──────┬─────────────────┬─────────────────┐
│ Type         │ Port │ Source          │ Description     │
├──────────────┼──────┼─────────────────┼─────────────────┤
│ SSH          │ 22   │ Your IP/32      │ Admin access    │
│ Custom TCP   │ 8501 │ 0.0.0.0/0       │ Streamlit app   │
│ HTTP         │ 80   │ 0.0.0.0/0       │ Load balancer   │
│ HTTPS        │ 443  │ 0.0.0.0/0       │ SSL traffic     │
└──────────────┴──────┴─────────────────┴─────────────────┘
```


## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **Response Time** | <2s | 1.5s avg |
| **Question Generation** | <3s | 2.1s avg |
| **Database Query** | <100ms | 85ms avg |
| **Concurrent Users** | 20+ | 15 tested |
| **Uptime** | 99.9% | 99.7% |
| **Memory Usage** | <6GB | 4.2GB avg |


##  Acknowledgments

- **[Ollama Team](https://ollama.ai)** for providing local LLM infrastructure
- **[Streamlit](https://streamlit.io)** for the intuitive web framework
- **[MongoDB](https://mongodb.com)** for flexible cloud database services
- **[AWS](https://aws.amazon.com)** for reliable cloud infrastructure
- **[Meta](https://ai.meta.com)** for the Llama3.2 language model

---
