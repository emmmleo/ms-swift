# Copyright (c) Alibaba, Inc. and its affiliates.
import asyncio
import os
import subprocess
import sys
import requests
from asyncio.subprocess import PIPE, STDOUT
from copy import deepcopy


async def run_and_get_log(*args, timeout=None):
    process = await asyncio.create_subprocess_exec(*args, stdout=PIPE, stderr=STDOUT)
    lines = []
    while True:
        try:
            line = await asyncio.wait_for(process.stdout.readline(), timeout)
        except asyncio.TimeoutError:
            break
        else:
            if not line:
                break
            else:
                lines.append(str(line))
    return process, lines


def run_command_in_subprocess(*args, timeout):
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    process, lines = loop.run_until_complete(run_and_get_log(*args, timeout=timeout))
    return (loop, process), lines


def close_loop(handler):
    loop, process = handler
    process.kill()
    loop.close()


def run_command_in_background_with_popen(command, all_envs, log_file):
    # Check for remote worker configuration
    remote_worker = os.environ.get('SWIFT_REMOTE_WORKER')
    if remote_worker:
        try:
            # Ensure the URL has a scheme
            if not remote_worker.startswith('http'):
                remote_worker = f'http://{remote_worker}'
            
            response = requests.post(
                f"{remote_worker}/launch",
                json={
                    "command": command,
                    "env": all_envs,
                    "log_file": log_file,
                    "work_dir": os.getcwd()
                },
                timeout=10
            )
            response.raise_for_status()
            print(f"Remote training launched successfully on {remote_worker}")
            return
        except Exception as e:
            print(f"Failed to launch remote training: {e}")
            raise e

    env = deepcopy(os.environ)
    if len(all_envs) > 0:
        for k, v in all_envs.items():
            env[k] = v
    daemon_kwargs = {}
    if sys.platform == 'win32':
        from subprocess import DETACHED_PROCESS, CREATE_NO_WINDOW
        daemon_kwargs['creationflags'] = DETACHED_PROCESS | CREATE_NO_WINDOW
        daemon_kwargs['close_fds'] = True
    else:
        daemon_kwargs['preexec_fn'] = os.setsid

    with open(log_file, 'w', encoding='utf-8') as f:
        subprocess.Popen(
            command, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True, bufsize=1, env=env)
