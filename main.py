import os
import subprocess
import time
import urllib.request
import tarfile
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

TS_VERSION = "1.62.0"
TS_DIR = f"/tmp/tailscale_{TS_VERSION}_amd64"

print("=== 1. MENGUNDUH & MENYIAPKAN TAILSCALE ===")
# Unduh Tailscale statis secara manual pakai Python (bypass curl)
if not os.path.exists(f"{TS_DIR}/tailscaled"):
    print(f"Mengunduh Tailscale v{TS_VERSION}...")
    url = f"https://pkgs.tailscale.com/stable/tailscale_{TS_VERSION}_amd64.tgz"
    urllib.request.urlretrieve(url, "/tmp/ts.tgz")
    
    print("Mengekstrak binary...")
    with tarfile.open("/tmp/ts.tgz", "r:gz") as tar:
        tar.extractall(path="/tmp")
    
    # Beri izin eksekusi
    os.chmod(f"{TS_DIR}/tailscaled", 0o755)
    os.chmod(f"{TS_DIR}/tailscale", 0o755)

print("=== 2. MENJALANKAN TAILSCALED (USERSPACE) ===")
os.makedirs("/tmp/ts_state", exist_ok=True)
tailscaled_process = subprocess.Popen([
    f"{TS_DIR}/tailscaled", 
    "--tun=userspace-networking", 
    "--statedir=/tmp/ts_state"
])

# Tunggu daemon menyala
time.sleep(3)

print("=== 3. LOGIN KE HEADSCALE & ENABLE SSH ===")
subprocess.run([
    f"{TS_DIR}/tailscale", "up",
    "--login-server=https://senvas.me",
    "--authkey=135f8db2998920da3ccdd5cb053e2805fc3c417c975010ba",
    "--ssh"
])
print("Tailscale terhubung!")

print("=== 4. MENJALANKAN PRECOMPILED MORI ===")
try:
    if os.path.exists("./Mori"):
        os.chmod("./Mori", 0o755)
    subprocess.Popen(["./Mori"])
    print("SUCCESS: ./Mori berjalan di background!")
except Exception as e:
    print(f"FATAL ERROR: Gagal menjalankan ./Mori! Alasan: {e}")

print("=== 5. MEMULAI FASTAPI PROXY ===")
app = FastAPI()
client = httpx.AsyncClient(base_url="http://localhost:3000")

@app.get("/bot")
def healthcheck():
    return {"status": "ok"}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_rust(request: Request, path: str):
    url = httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8"))
    req = client.build_request(
        request.method,
        url,
        headers=request.headers.raw,
        content=await request.body()
    )
    r = await client.send(req, stream=True)
    return StreamingResponse(
        r.aiter_raw(),
        status_code=r.status_code,
        headers=r.headers,
        background=BackgroundTask(r.aclose)
    )
