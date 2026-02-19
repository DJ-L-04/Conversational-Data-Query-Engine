import os
import uuid
import json
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.db.base import get_db
from app.models.models import User, UploadedFile
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.schemas.schemas import FileUploadResponse

router = APIRouter(prefix="/files", tags=["Files"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/upload", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")

    content = await file.read()
    size_kb = len(content) / 1024

    if size_kb / 1024 > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        row_count = len(df)
        column_count = len(df.columns)
        columns = df.columns.tolist()
    except Exception:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Could not parse file. Ensure it is a valid CSV or Excel.")

    record = UploadedFile(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_type=ext.lstrip("."),
        row_count=row_count,
        column_count=column_count,
        columns_json=json.dumps(columns),
        file_size_kb=round(size_kb, 2)
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return FileUploadResponse(
        id=record.id,
        filename=record.filename,
        original_filename=record.original_filename,
        file_type=record.file_type,
        row_count=row_count,
        column_count=column_count,
        columns=columns,
        file_size_kb=record.file_size_kb,
        uploaded_at=record.uploaded_at
    )


@router.get("/", response_model=List[FileUploadResponse])
def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    files = db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id).all()
    result = []
    for f in files:
        columns = json.loads(f.columns_json) if f.columns_json else []
        result.append(FileUploadResponse(
            id=f.id,
            filename=f.filename,
            original_filename=f.original_filename,
            file_type=f.file_type,
            row_count=f.row_count,
            column_count=f.column_count,
            columns=columns,
            file_size_kb=f.file_size_kb,
            uploaded_at=f.uploaded_at
        ))
    return result


@router.delete("/{file_id}", status_code=204)
def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    if os.path.exists(record.file_path):
        os.remove(record.file_path)

    db.delete(record)
    db.commit()
