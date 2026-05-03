
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import Category, Game, Progress, Subcategory, get_db
from utils import save_file

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _require_user(request: Request):
    return request.cookies.get("user_id")


@router.get("/categories")
async def view_categories(request: Request, db: Session = Depends(get_db)):
    if not _require_user(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request=request,
        name="categories.html",
        context={"categories": db.query(Category).all()},
    )


@router.get("/subcategory/{subcat_id}")
async def view_subcategory(
    subcat_id: int, request: Request, db: Session = Depends(get_db)
):
    user_id = _require_user(request)
    if not user_id:
        return RedirectResponse(url="/login")
    progress_ids = [
        p.game_id
        for p in db.query(Progress).filter(Progress.user_id == int(user_id)).all()
    ]
    return templates.TemplateResponse(
        request=request,
        name="subcategory.html",
        context={
            "subcategory": db.query(Subcategory).filter(Subcategory.id == subcat_id).first(),
            "games": db.query(Game).filter(Game.subcategory_id == subcat_id).all(),
            "completed_game_ids": progress_ids,
        },
    )


@router.get("/game/{game_id}")
async def play_game(game_id: int, request: Request, db: Session = Depends(get_db)):
    if not _require_user(request):
        return RedirectResponse(url="/login")
    game = db.query(Game).filter(Game.id == game_id).first()
    return templates.TemplateResponse(
        request=request,
        name="play.html",
        context={"game": game, "subcategory_id": game.subcategory_id},
    )


@router.post("/progress/{game_id}")
async def save_progress(
    game_id: int, request: Request, db: Session = Depends(get_db)
):
    user_id = _require_user(request)
    if user_id:
        exists = (
            db.query(Progress)
            .filter_by(user_id=int(user_id), game_id=game_id)
            .first()
        )
        if not exists:
            db.add(Progress(user_id=int(user_id), game_id=game_id))
            db.commit()
    return {"status": "ok"}


@router.get("/games")
async def all_games(request: Request, db: Session = Depends(get_db)):
    if not _require_user(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request=request,
        name="games.html",
        context={"games": db.query(Game).all()},
    )


@router.get("/add_game/{subcategory_id}")
def user_add_game_page(
    subcategory_id: int, request: Request, db: Session = Depends(get_db)
):
    if not _require_user(request):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request=request,
        name="add_game.html",
        context={
            "subcategories": db.query(Subcategory).all(),
            "form_action": "/add_game",
            "preselected_id": subcategory_id,
        },
    )


@router.post("/add_game")
async def user_add_game(
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
    return RedirectResponse(url=f"/subcategory/{subcategory_id}", status_code=303)
