import base64
import logging

import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from tortoise.contrib.fastapi import register_tortoise

from helpers.design import templates

from endpoints import stories, giveaways, submissions, server_setup

import settings
import aiohttp

app = FastAPI()

logging.basicConfig(level=logging.INFO)


load_dotenv()

app = FastAPI(
    docs_url=None,
    redoc_url="/docs",
    title=f"{settings.SERVER_METADATA.get('name', 'Chatfic Server')} API - chatficDB",
    description="This API server is created with the open source project chatficDB.",
    version=settings.CHATFICDB_VERSION_NAME,
    contact=settings.SERVER_METADATA.get("contact", {}),
    license_info={
        "name": "MIT License",
        "url": "https://raw.githubusercontent.com/gokhanmeteerturk/chatficdb"
               "/refs/heads/main/LICENSE",
    },
    openapi_tags=[
    {
        "name": "stories & series",
        "description": "Operations for stories and series.",
    },
    {
        "name": "html",
        "description": "Pages with html response."
    },
    {
        "name": "misc",
        "description": "Managing miscellaneous operations."
    },
]
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(stories.router)
app.include_router(submissions.router)
app.include_router(giveaways.router)
app.include_router(server_setup.router)

server_url = settings.SERVER_METADATA["url"]
if server_url.endswith("/"):
    server_url = server_url[:-1]
if not server_url.startswith("https://"):
    if not server_url.startswith("http://"):
        server_url = "https://" + server_url

origins = ["https://chatficlab.com", "https://api.chatficlab.com", server_url]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


S3_LINK = settings.S3_LINK

@app.options("/stories")
async def preflight_stories():
    return Response(status_code=204)

@app.get("/submit", response_class=HTMLResponse, tags=["html"])
async def show_submit_page(request: Request):
    metadata = settings.SERVER_METADATA

    return templates.TemplateResponse(
        "submit_page.html",
        {"request": request},
    )

@app.get("/submissions", response_class=HTMLResponse, tags=["html"])
async def show_submissions_page(request: Request):
    return templates.TemplateResponse(
        "submissions.html",
        {"request": request},
    )



register_tortoise(
    app,
    config=settings.TORTOISE_CONFIG,
    modules={"models": ["database.models"]},
    generate_schemas=True,
    add_exception_handlers=False,
)


@app.on_event("startup")
async def startup_register_chatficdb():

    if not settings.REGISTER_ON_STARTUP:
        return

    if os.path.exists(settings.REGISTERED_PUBLIC_KEY_FILE):
        return  # Already registered

    try:
        payload = {
            "secret": settings.SECRET_KEY,
            "slug": settings.SERVER_METADATA["slug"],
            "title": settings.SERVER_METADATA["name"],
            "url": settings.SERVER_METADATA["url"],
            "nsfw": settings.SERVER_METADATA["nsfw"]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.CHATFICLAB_BACKEND_URL}/register-chatficdb",
                json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()

            reconstructed_public_key = Ed25519PublicKey.from_public_bytes(
                base64.b64decode(data["public_key"]))
            pem_public = reconstructed_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            with open(settings.REGISTERED_PUBLIC_KEY_FILE, "wb") as f:
                f.write(pem_public)
            print("✅ Chatfic Server registered on startup.")
    except Exception as e:
        print(f"❌ Failed to register on startup: {e}")
