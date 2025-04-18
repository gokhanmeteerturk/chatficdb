import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from tortoise.contrib.fastapi import register_tortoise
from helpers.design import templates

from endpoints import stories, giveaways, submissions

import settings

app = FastAPI()

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

S3_LINK = settings.S3_LINK

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
