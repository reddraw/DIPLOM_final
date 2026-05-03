
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import Category, Game, Progress, Subcategory, User, get_db
from utils import get_password_hash, save_file

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")


def _ctx(db: Session, **extra) -> dict:

    return {
        "categories": db.query(Category).all(),
        "subcategories": db.query(Subcategory).all(),
        "games": db.query(Game).all(),
        "users": db.query(User).all(),
        **extra,
    }




@router.get("")
def admin_panel(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request, name="admin.html", context=_ctx(db)
    )




@router.post("/add_user")
def add_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse(
            request=request,
            name="admin.html",
            context=_ctx(db, error=f"Пользователь «{username}» уже существует!"),
        )
    db.add(User(username=username, password=get_password_hash(password)))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/edit_user/{user_id}")
def edit_user_page(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse(
        request=request, name="edit_user.html", context={"user": user}
    )


@router.post("/edit_user/{user_id}")
def edit_user(
    user_id: int,
    username: str = Form(...),
    new_password: str = Form(None),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.username = username
        if new_password:
            user.password = get_password_hash(new_password)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/delete_user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.query(Progress).filter(Progress.user_id == user_id).delete()
        db.delete(user)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)


# ── Разделы ──────────────────────────────────────────────────────────────────

@router.post("/add_category")
def add_category(name: str = Form(...), db: Session = Depends(get_db)):
    db.add(Category(name=name))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/edit_category/{cat_id}")
def edit_category(cat_id: int, name: str = Form(...), db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if cat:
        cat.name = name
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)


# ── Подразделы ────────────────────────────────────────────────────────────────

@router.post("/add_subcategory")
def add_subcategory(
    name: str = Form(...), category_id: int = Form(...), db: Session = Depends(get_db)
):
    db.add(Subcategory(name=name, category_id=category_id))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/edit_subcategory/{sub_id}")
def edit_subcategory(
    sub_id: int, name: str = Form(...), db: Session = Depends(get_db)
):
    sub = db.query(Subcategory).filter(Subcategory.id == sub_id).first()
    if sub:
        sub.name = name
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)


# ── Игры ─────────────────────────────────────────────────────────────────────

@router.get("/add_game_page")
def add_game_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="add_game.html",
        context={
            "subcategories": db.query(Subcategory).all(),
            "form_action": "/admin/add_game",
            "preselected_id": None,
        },
    )


@router.post("/add_game")
async def add_game(
    subcategory_id: int = Form(...),
    name: str = Form(...),
    game_type: str = Form(...),
    question: str = Form(...),
    correct_answer: str = Form(...),
    options: str = Form(""),
    image_file: UploadFile = File(None),
    audio_file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    game_data = {
        "type": game_type,
        "question": question,
        "correct_answer": correct_answer,
        "options": options,
        "image": save_file(image_file, "images"),
        "audio": save_file(audio_file, "audio"),
    }
    db.add(Game(name=name, subcategory_id=subcategory_id, game_data=game_data))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/edit_game/{game_id}")
def edit_game_page(game_id: int, request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="edit_game.html",
        context={
            "game": db.query(Game).filter(Game.id == game_id).first(),
            "subcategories": db.query(Subcategory).all(),
        },
    )


@router.post("/edit_game/{game_id}")
async def edit_game(
    game_id: int,
    subcategory_id: int = Form(...),
    name: str = Form(...),
    question: str = Form(...),
    correct_answer: str = Form(...),
    image_file: UploadFile = File(None),
    audio_file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        game.name = name
        game.subcategory_id = subcategory_id
        data = game.game_data.copy()
        data["question"] = question
        data["correct_answer"] = correct_answer
        img = save_file(image_file, "images")
        aud = save_file(audio_file, "audio")
        if img:
            data["image"] = img
        if aud:
            data["audio"] = aud
        game.game_data = data
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/delete_game/{game_id}")
def delete_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        db.query(Progress).filter(Progress.game_id == game_id).delete()
        db.delete(game)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)
