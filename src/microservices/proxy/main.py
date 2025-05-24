import os
import random
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()

MONOLITH_URL = os.getenv("MONOLITH_URL", "http://monolith:8080")
MOVIES_SERVICE_URL = os.getenv("MOVIES_SERVICE_URL", "http://movies-service:8081")
GRADUAL_MIGRATION = os.getenv("GRADUAL_MIGRATION", "false").lower() == "true"
MOVIES_MIGRATION_PERCENT = int(os.getenv("MOVIES_MIGRATION_PERCENT", "0"))

@app.get("/health")
async def health_check():
    return {"status": True}

@app.api_route("/api/movies", methods=["GET"])
@app.api_route("/api/movies/", methods=["GET"])
async def proxy_movies(request: Request) -> Response:
    use_new_service = False
    if GRADUAL_MIGRATION:
        chance = random.randint(1, 100)
        use_new_service = chance <= MOVIES_MIGRATION_PERCENT
        print(f"[Router] 🎯 Random {chance} → using {'MOVIES' if use_new_service else 'MONOLITH'}")

    target_url = f"{MOVIES_SERVICE_URL}/api/movies" if use_new_service else f"{MONOLITH_URL}/api/movies"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(target_url)
        print(f"[Proxy] ↪ Forwarded to: {target_url} (Status {response.status_code})")
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response.headers,
            media_type=response.headers.get("content-type", "application/json")
        )
    except httpx.RequestError as e:
        print(f"[Error] ❌ Failed to fetch from {target_url}: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": "Bad Gateway", "details": str(e)}
        )

@app.api_route("/api/users", methods=["GET"])
@app.api_route("/api/users/", methods=["GET"])
async def proxy_users(request: Request) -> Response:
    target_url = f"{MONOLITH_URL}/api/users"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(target_url)
        print(f"[Proxy] ↪ Forwarded to: {target_url} (Status {response.status_code})")
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response.headers,
            media_type=response.headers.get("content-type", "application/json")
        )
    except httpx.RequestError as e:
        print(f"[Error] ❌ Failed to fetch from {target_url}: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": "Bad Gateway", "details": str(e)}
        )
