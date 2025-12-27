import os
import subprocess
import time
import psutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List
import logging
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainRequest(BaseModel):
    command: List[str]
    env: Dict[str, str]
    log_file: str
    work_dir: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    # Mock authentication
    if request.username == "admin" and request.password == "swift":
        return {"token": "mock-token-12345", "username": "admin"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

class KillRequest(BaseModel):
    pid: int
    output_dir: str

@app.post("/launch")
async def launch_training(request: TrainRequest):
    try:
        # Ensure the directory for log file exists
        log_dir = os.path.dirname(request.log_file)
        os.makedirs(log_dir, exist_ok=True)

        # Prepare environment variables
        env = os.environ.copy()
        env.update(request.env)

        # Launch the process
        # We use nohup logic similar to local execution
        with open(request.log_file, 'w', encoding='utf-8') as f:
            # On Windows, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP might be needed
            # On Linux, preexec_fn=os.setsid creates a new session
            kwargs = {}
            if os.name != 'nt':
                kwargs['preexec_fn'] = os.setsid
            
            process = subprocess.Popen(
                request.command,
                stdout=f,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                env=env,
                cwd=request.work_dir or os.getcwd(),
                **kwargs
            )
        
        return {
            "status": "success", 
            "message": "Training started", 
            "pid": process.pid,
            "log_file": request.log_file
        }
    except Exception as e:
        logger.error(f"Failed to launch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks")
async def list_tasks(group: Optional[str] = None):
    """
    List running tasks similar to Runtime.refresh_tasks
    """
    process_name = 'swift'
    negative_names = ['swift.exe', 'swift-script.py']
    
    if group == 'llm_train':
        cmd_name = ['pt', 'sft']
    elif group == 'llm_rlhf':
        cmd_name = ['rlhf']
    elif group == 'llm_infer':
        cmd_name = ['infer', 'deploy']
    elif group == 'llm_export':
        cmd_name = ['export']
    else:
        cmd_name = ['pt', 'sft', 'rlhf', 'infer', 'deploy', 'export', 'eval']
    
    tasks = []
    
    for proc in psutil.process_iter():
        try:
            cmdlines = proc.cmdline()
        except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess):
            continue
            
        # Filter logic copied from Runtime.refresh_tasks
        if any([process_name in cmdline for cmdline in cmdlines]) and \
           not any([neg in cmdline for neg in negative_names for cmdline in cmdlines]) and \
           any([c in cmdline for c in cmd_name for cmdline in cmdlines]):
            
            if any([group == 'llm_rlhf' and 'grpo' in cmdline for cmdline in cmdlines]):
                continue
            if group == 'llm_grpo' and all(['grpo' not in cmdline for cmdline in cmdlines]):
                continue
                
            # Construct task info string
            pid = proc.pid
            ts = time.time()
            try:
                create_time = proc.create_time()
                create_time_formatted = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d, %H:%M')
                
                # Calculate running time format like 1d:2h:30m
                running_seconds = ts - create_time
                m, s = divmod(running_seconds, 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)
                if d > 0:
                    running_time = f'{int(d)}d:{int(h)}h:{int(m)}m'
                elif h > 0:
                    running_time = f'{int(h)}h:{int(m)}m'
                else:
                    running_time = f'{int(m)}m'

                task_str = f'pid:{pid}/create:{create_time_formatted}/running:{running_time}/cmd:{" ".join(proc.cmdline())}'
                tasks.append(task_str)
            except Exception:
                continue

    return {"tasks": tasks}

@app.get("/log")
async def get_log(log_file: str, offset: int = 0, limit: int = 2000):
    """
    Read log file content
    """
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="Log file not found")
    
    try:
        # Use binary mode to safely seek
        with open(log_file, 'rb') as f:
            f.seek(offset)
            content_bytes = f.read(limit)
            
        # Decode to string, ignore errors at boundaries
        content = content_bytes.decode('utf-8', errors='ignore')
        
        return {"content": content, "length": len(content_bytes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/kill")
async def kill_task(request: KillRequest):
    try:
        pid = request.pid
        if os.name == 'nt':
            subprocess.run(['taskkill', '/f', '/t', '/pid', str(pid)], check=True)
        else:
            # We use the output_dir to find pkill pattern if pid fails, 
            # but usually killing by PID is safer if we know it.
            # However, the original code used pkill -f output_dir for Linux.
            # Let's try PID first which is more specific.
            try:
                os.killpg(os.getpgid(pid), 9)
            except ProcessLookupError:
                # Fallback to pkill if process group not found
                subprocess.run(['pkill', '-9', '-f', request.output_dir], check=True)
                
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to kill task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from swift.llm.model.register import get_all_models
from swift.llm.dataset.register import get_dataset_list

@app.get("/models")
async def list_models():
    """Get all supported models"""
    return {"models": get_all_models()}

@app.get("/datasets")
async def list_datasets():
    """Get all supported datasets"""
    return {"datasets": get_dataset_list()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
