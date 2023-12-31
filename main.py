# main.py

import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from tortoise.contrib.fastapi import register_tortoise

from endpoints import stories, giveaways

import settings

app = FastAPI()

templates = Jinja2Templates(directory="templates")
templates.env.globals['server'] = settings.SERVER_METADATA
templates.env.globals['theme'] = settings.THEME

logging.basicConfig(level=logging.INFO)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(stories.router)
app.include_router(giveaways.router)

S3_LINK = settings.S3_LINK


@app.get("/submit", response_class=HTMLResponse)
async def show_submit_page(request: Request):
    metadata = settings.SERVER_METADATA

    return templates.TemplateResponse(
        "submit_page.html",
        {"request": request},
    )


register_tortoise(
    app,
    config=settings.TORTOISE_CONFIG,
    modules={"models": ["database.models"]},
    generate_schemas=True,
    add_exception_handlers=False,
)
