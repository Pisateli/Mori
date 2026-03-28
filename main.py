import os
import subprocess
from fastapi import FastAPI

# --- FUNGSI DIAGNOSTIK ---
def run_diag(command):
    print(f"\n--- EXEC: {command} ---")
    try:
        # Menjalankan command dan mengambil outputnya
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        print(result.decode())
    except Exception as e:
        print(f"Error/Not Found: {e}")

print("=== STARTING ENVIRONMENT DIAGNOSTICS ===")

# List perintah yang kamu minta
commands = [
    "cat /etc/os-release", # OS Info
    "whoami",             # Username
    "free -h",            # RAM
    "lscpu",              # CPU Info
    "df -h",              # Disk Space
    "nvidia-smi"          # GPU Info (Jika ada)
]

for cmd in commands:
    run_diag(cmd)

print("=== DIAGNOSTICS COMPLETE ===")

# --- MINIMAL FASTAPI (Agar Cerebrium Tetap Jalan) ---
app = FastAPI()

@app.get("/bot")
def healthcheck():
    return {"status": "diag_complete"}

@app.get("/")
def read_root():
    return {"message": "Cek log di dashboard untuk hasil diagnosa!"}
