from fastapi import APIRouter

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

import settings

router = APIRouter()


templates = Jinja2Templates(directory="templates")
templates.env.globals['server'] = settings.SERVER_METADATA
templates.env.globals['theme'] = settings.THEME

@router.get("/giveaway", response_class=HTMLResponse, tags=["html"])
async def giveaway(request: Request):
    return templates.TemplateResponse(
        "giveaway_page.html",
        {"request": request},
    )
