from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inicio/", response_class=HTMLResponse)
async def portal_view(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
