# SkyForge Web UI

A modern Vue.js frontend for SkyForge.

## Project Setup

### Prerequisites
- Docker
- Python backend (`agent.py`) running on port 8000

### Build and Run with Docker

1. **Build the Docker image:**
   ```bash
   docker build -t skyforge-web-ui .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 8080:80 skyforge-web-ui
   ```

3. **Access the UI:**
   Open [http://localhost:8080](http://localhost:8080) in your browser.

### Backend Setup

Ensure the SkyForge Agent is running:
```bash
python ../swift/ui/agent.py
```
The agent should be listening on `http://0.0.0.0:8000`.

### Development (if Node.js is installed)

```bash
npm install
npm run dev
```

## Features
- **Login**: Simple authentication (Default: SkyForge / 123456)
- **Dashboard**: Navigation to training modules
- **Training**: Launch SFT/RLHF training tasks and view real-time logs
