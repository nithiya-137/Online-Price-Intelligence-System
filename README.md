# Online Price Intelligence System

A professional price comparison and intelligence platform that aggregates data from multiple e-commerce stores (Amazon, eBay, Flipkart, Meesho, and more) using advanced scraping and image recognition.

## 📁 Project Structure

- `frontend/`: React (Vite) frontend application.
- `backend-express/`: Express.js server for Authentication and Database management.
- `backend/`: Python FastAPI service for Scrapers, Image Recognition (AI), and Background Tasks.
- `docs/`: Technical documentation, implementation guides, and optimization reports.
- `scripts/`: Diagnostic and maintenance scripts.
- `legacy/`: Old CLI-based scrapers and startup scripts.

## 🚀 Quick Start (Docker - Recommended)

The easiest way to run the entire system is using Docker Compose.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### Launching the Application
1. Open your terminal in the project root.
2. Run the following command:
   ```bash
   docker-compose up --build
   ```
3. Once containers are running:
   - **Frontend**: [http://localhost:5173](http://localhost:5173)
   - **Express API**: [http://localhost:5001](http://localhost:5001)
   - **Python API**: [http://localhost:8000](http://localhost:8000)
   - **Celery Flower (Monitoring)**: [http://localhost:5555](http://localhost:5555)

## 🛠️ Manual Development Setup

If you prefer to run services individually for development:

### 1. PostgreSQL & Redis
Ensure you have PostgreSQL running on port 5432 and Redis on 6379.

### 2. Express Backend
```bash
cd backend-express
npm install
npm run dev
```

### 3. Python Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate # macOS/Linux
pip install -r requirements.txt
python -m uvicorn app.main_optimized:app --reload --port 8000
```

### 4. React Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📝 Environment Variables
Each service (`backend`, `backend-express`, `frontend`) has its own `.env.example` file. Copy these to `.env` and fill in the required credentials (DB_PASSWORD, API_KEYS, etc.).

## 🤝 Team Contribution
- **Naming Convention**: Use camelCase for JS/TS and snake_case for Python.
- **Documentation**: If you add a new feature, update the corresponding module in `docs/`.
- **Scripts**: Use the `scripts/` folder for one-off data migrations or diagnostic tools.
