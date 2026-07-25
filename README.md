# CAIP-Karnataka Intelligence Platform

CAIP-Karnataka (Crime Analysis & Intelligence Platform) is a full-stack intelligence dashboard and analytics tool built for law enforcement agencies. It provides a visual dashboard for historical district crime statistics and an intelligence module capable of parsing unstructured PDF police dossiers to automatically extract and map criminal networks and repeat offenders.

## Setup Instructions

You can run this platform either using Docker (recommended) or natively on your local machine.

### Option 1: Docker Setup (Recommended)

**Prerequisites:**
- **Docker**
- **Docker Compose**

**Steps:**
1. Clone the repository and navigate to the root directory.
2. Build and start the application:
   ```bash
   docker compose up -d --build
   ```
   This will spin up three containers:
   - `postgres`: PostgreSQL + PostGIS database.
   - `backend`: FastAPI Python server (running on port `8000`).
   - `frontend`: React/Vite development server (running on port `5173`).

3. Access the application in your browser at [http://localhost:5173](http://localhost:5173).

4. To stop the application, run:
   ```bash
   docker compose down
   ```

### Option 2: Local Native Setup

**Prerequisites:**
- **Python 3.10+**
- **Node.js (v18+)**
- **PostgreSQL** (running locally)

**Backend Setup:**
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set your environment variables. Ensure your PostgreSQL database is running and accessible. By default, the app looks for:
   `DATABASE_URL=postgresql+asyncpg://caip_user:caip_password@localhost:5432/caip_karnataka`
5. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

**Frontend Setup:**
1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the Node dependencies:
   ```bash
   npm install
   ```
3. Ensure the `VITE_API_BASE_URL` environment variable is set to `http://localhost:8000/api/v1` (e.g. via `.env`).
4. Start the development server:
   ```bash
   npm run dev
   ```
5. Access the application at [http://localhost:5173](http://localhost:5173).

## Core Workflows

### 1. Uploading Historical CSV Data
The dashboard requires historical crime data to render the Executive Dashboard and Anomaly Alerts.
- Go to the **Upload Data** page.
- Select and upload a valid OGD Platform India CSV file (e.g., `2013.csv`).
- The system will process the file, map it to the correct districts, and automatically populate the database.
- Navigate to the **Executive Dashboard** to view the parsed trends and rankings.

### 2. Uploading Intelligence PDFs
The system includes an NLP parser capable of extracting accused entities and their associations from unstructured text.
- If you do not have a real dossier, you can generate a sample one for testing. 
  - *If using Docker:* `docker compose exec backend python scripts/generate_intelligence_report.py`
  - *If native:* `python backend/scripts/generate_intelligence_report.py`
  This will create `data/raw/Case_Dossier_Alpha.pdf`.
- Go to the **Upload Data** page and upload this PDF.
- Navigate to the **Criminal Network** page to view an interactive force-directed graph of the extracted gangs and associations.
- Navigate to the **Repeat Offenders** page to see a ranked list of the most active offenders and their associated risk levels.
