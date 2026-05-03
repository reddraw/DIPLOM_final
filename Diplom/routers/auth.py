
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import User, get_db
from utils import get_password_hash, verify_password

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/register")
def reg_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html", context={"is_register": True}
    )


@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Логин уже занят", "is_register": True},
        )
    db.add(User(username=username, password=get_password_hash(password)))
    db.commit()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html", context={"is_register": False}
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password):
        response = RedirectResponse(url="/categories", status_code=303)
        response.set_cookie(key="user_id", value=str(user.id))
        return response
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": "Неверный логин или пароль", "is_register": False},
    )


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user_id")
    return response
