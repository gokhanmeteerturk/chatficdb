import base64

import aiohttp
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import os
import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.globals['server'] = settings.SERVER_METADATA
templates.env.globals['theme'] = settings.THEME

@router.get("/setup", response_class=HTMLResponse, tags=["setup"])
async def setup_page(request: Request):
    print(f"{settings.CHATFICLAB_BACKEND_URL}/register-chatficdb")
    if os.path.exists(settings.REGISTERED_PUBLIC_KEY_FILE):
        raise HTTPException(status_code=404, detail="Page Not Found")
    return templates.TemplateResponse("setup.html", {"request": request})

@router.post("/complete-setup", tags=["setup"])
async def complete_setup():
    if os.path.exists(settings.REGISTERED_PUBLIC_KEY_FILE):
        return JSONResponse(status_code=400, content={"error": "Already registered."})

    payload = {
        "secret": settings.SECRET_KEY,
        "slug": settings.SERVER_METADATA["slug"],
        "title": settings.SERVER_METADATA["name"],
        "url": settings.SERVER_METADATA["url"],
        "nsfw": settings.SERVER_METADATA["nsfw"]
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{settings.CHATFICLAB_BACKEND_URL}/register-chatficdb", json=payload) as response:
                response.raise_for_status()  # Raises aiohttp.ClientResponseError on HTTP error status

                data = await response.json()

            reconstructed_public_key = Ed25519PublicKey.from_public_bytes(
                base64.b64decode(data["public_key"]))
            pem_public = reconstructed_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            with open(settings.REGISTERED_PUBLIC_KEY_FILE, "wb") as f:
                f.write(pem_public)

            return JSONResponse(content={"message": "Registration successful", "data": data})

        except aiohttp.ClientResponseError as e:
            print(f"HTTP error: {e.status} - {e.message}")
            return JSONResponse(status_code=e.status, content={"error": f"HTTP error {e.status}"})
        except Exception as e:
            raise e
            return JSONResponse(status_code=500, content={"error": str(e)})
