import subprocess
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

subprocess.Popen(["./Mori"])

app = FastAPI()
client = httpx.AsyncClient(base_url="http://localhost:3000")

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
