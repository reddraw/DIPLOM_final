
import asyncio
import os
import sys

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers import admin, auth, games
for folder in ["uploads/images", "uploads/audio"]:
    os.makedirs(folder, exist_ok=True)

app = FastAPI(title="Образовательная веб-платформа")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(games.router)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
