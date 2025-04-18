import settings
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
templates.env.globals['server'] = settings.SERVER_METADATA
templates.env.globals['theme'] = settings.THEME