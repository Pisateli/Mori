import os
import subprocess
import time
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

print("=== 1. MENGINSTALL TAILSCALE ===")
# Instal Tailscale (mengabaikan error systemd karena kita di dalam container)
os.system("curl -fsSL https://tailscale.com/install.sh | sh")

print("=== 2. MENJALANKAN TAILSCALED (USERSPACE) ===")
# Buat direktori state di /tmp karena /var/lib biasanya read-only/butuh root
os.makedirs("/tmp/tailscale", exist_ok=True)

# Jalankan daemon Tailscale di background
tailscaled_process = subprocess.Popen([
    "tailscaled", 
    "--tun=userspace-networking", 
    "--statedir=/tmp/tailscale"
])

# Beri waktu beberapa detik agar daemon Tailscale siap menerima perintah
time.sleep(3)

print("=== 3. LOGIN KE HEADSCALE & ENABLE SSH ===")
# Login tanpa sudo dan aktifkan SSH
subprocess.run([
    "tailscale", "up",
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
