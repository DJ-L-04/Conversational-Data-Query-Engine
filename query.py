import uuid
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.base import get_db
from app.models.models import User, UploadedFile, QueryHistory
from app.core.dependencies import get_current_user
from app.schemas.schemas import QueryRequest, QueryResponse, QueryHistoryResponse
from app.services.query_service import get_cached_answer, cache_answer, query_dataframe

router = APIRouter(prefix="/query", tags=["Query"])

ALLOWED_MODELS = {"gpt-3.5-turbo", "gpt-4"}


@router.post("/", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail=f"Model must be one of {ALLOWED_MODELS}")

    file_record = db.query(UploadedFile).filter(
        UploadedFile.id == payload.file_id,
        UploadedFile.user_id == current_user.id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    cached = get_cached_answer(str(payload.file_id), payload.question)
    start = time.time()

    if cached:
        answer = cached["answer"]
        is_cached = True
    else:
        try:
            answer = query_dataframe(
                file_path=file_record.file_path,
                file_type=file_record.file_type,
                question=payload.question,
                model=payload.model
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

        cache_answer(str(payload.file_id), payload.question, answer)
        is_cached = False

    response_time_ms = (time.time() - start) * 1000

    history = QueryHistory(
        file_id=payload.file_id,
        user_id=current_user.id,
        question=payload.question,
        answer=answer,
        model_used=payload.model,
        cached=is_cached,
        response_time_ms=round(response_time_ms, 2)
    )
    db.add(history)
    db.commit()

    return QueryResponse(
        answer=answer,
        file_id=payload.file_id,
        question=payload.question,
        model_used=payload.model,
        cached=is_cached,
        response_time_ms=round(response_time_ms, 2)
    )


@router.get("/history/{file_id}", response_model=List[QueryHistoryResponse])
def get_history(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return db.query(QueryHistory).filter(
        QueryHistory.file_id == file_id,
        QueryHistory.user_id == current_user.id
    ).order_by(QueryHistory.created_at.desc()).all()


@router.get("/history", response_model=List[QueryHistoryResponse])
def get_all_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(QueryHistory).filter(
        QueryHistory.user_id == current_user.id
    ).order_by(QueryHistory.created_at.desc()).limit(50).all()
