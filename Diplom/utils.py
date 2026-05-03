
import uuid
import shutil

import bcrypt
from fastapi import UploadFile


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def save_file(file: UploadFile, folder: str):
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit(".", 1)[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = f"uploads/{folder}/{filename}"
    with open(path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
    return f"/{path}"
