# main.py

import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from tortoise.contrib.fastapi import register_tortoise

from endpoints import stories

import settings

app = FastAPI()

templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(products.router)
# app.include_router(orders.router)

load_dotenv()

app = FastAPI()
app.include_router(stories.router)

S3_LINK = "https://topaltdb.s3.us-east-2.amazonaws.com"


@app.get("/submit", response_class=HTMLResponse)
async def show_submit_page(request: Request):
    metadata = settings.SERVER_METADATA

    # Pass the template and context data to the template engine
    return templates.TemplateResponse(
        "submit_page.html",
        {"request": request, "metadata": metadata},
    )


register_tortoise(
    app,
    config=settings.TORTOISE_CONFIG,
    modules={"models": ["database.models"]},
    generate_schemas=True,
    add_exception_handlers=False,
)
