# Financial Analyzer Pro - Execution Guide

## 🔧 Prerequisites
- Python 3.8 or higher
- pip package manager

## 🚀 Step-by-Step Execution

### 1. Clone and Setup
```bash
git clone <your-repository-url>
cd financial-analyzer-pro
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
---

📄 docs/EXECUTION_GUIDE.md

```markdown
# Financial Analyzer Pro - Execution Guide

## 🔧 Prerequisites
- Python 3.8 or higher
- pip package manager

## 🚀 Step-by-Step Execution

### 1. Clone and Setup
```bash
git clone <your-repository-url>
cd financial-analyzer-pro
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-api.txt
```

3. Verify Project Structure

```bash
ls -la
```

Expected:

```
README.md, requirements.txt, config.py, main.py, run_server.py, src/
```

4. Test Imports

```bash
python -c "from src.core.crisis_analyzer import CrisisAnalyzer; print('✅ CrisisAnalyzer OK')"
python -c "from src.core.monte_carlo import MonteCarloEngine; print('✅ MonteCarloEngine OK')"
python -c "from src.api.routes import api_router; print('✅ API Router OK')"
```

5. Run the Server

```bash
python run_server.py
```

6. Expected Output

```
🚀 Starting Financial Analyzer Pro Server...
📊 Application: Financial Analyzer Pro
🔢 Version: 1.0.0
👨‍💻 Developer: Seyed Aladdin Mousavi Jashni
🔧 Initializing core modules...
✅ All core modules initialized successfully!
✅ Server started successfully!
📚 API Docs: http://localhost:8000/api/docs
🔍 Health: http://localhost:8000/api/system/health
```

7. Test the API

```bash
# New terminal:
curl http://localhost:8000/api/system/health
```

Expected:

```json
{"status":"healthy","timestamp":"2024-...","version":"1.0.0"}
```

8. Access Documentation

Open browser: http://localhost:8000/api/docs

🛠️ Troubleshooting

ModuleNotFoundError

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python run_server.py
```

Port 8000 Busy

```bash
python run_server.py --port 8080
```

Permission Issues

```bash
chmod +x run_server.py
chmod -R 755 src/
```

✅ Verification Checklist

· Virtual environment activated
· Dependencies installed
· Imports work without errors
· Server starts successfully
· Health endpoint responds
· API docs accessible

Happy Coding! 🚀

