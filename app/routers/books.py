from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..database import get_db
from .. import models
from ..schemas import BookCreate, BookOut, BookUpdate

router = APIRouter(prefix="/books", tags=["books"])

def _get_book_or_404(db: Session, book_id: int) -> models.Book:
    book = db.get(models.Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book

def _ensure_author_exists(db: Session, author_id: int):
    if not db.get(models.Author, author_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found")

@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    # author must exist
    _ensure_author_exists(db, payload.author_id)

    existing = db.execute(
        select(models.Book).where(func.lower(models.Book.isbn) == func.lower(payload.isbn.strip()))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ISBN already exists")

    book = models.Book(
        title=payload.title.strip(),
        isbn=payload.isbn.strip(),
        publication_year=payload.publication_year,
        available_copies=payload.available_copies if payload.available_copies is not None else 1,
        author_id=payload.author_id,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

@router.get("", response_model=List[BookOut])
def list_books(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="search in title"),
    author_id: Optional[int] = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(models.Book)
    if q:
        stmt = stmt.where(models.Book.title.ilike(f"%{q.strip()}%"))
    if author_id:
        stmt = stmt.where(models.Book.author_id == author_id)
    stmt = stmt.order_by(models.Book.title.asc()).limit(limit).offset(offset)
    books = db.execute(stmt).scalars().all()
    return books

@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    return _get_book_or_404(db, book_id)

@router.put("/{book_id}", response_model=BookOut)
def update_book(book_id: int, payload: BookUpdate, db: Session = Depends(get_db)):
    book = _get_book_or_404(db, book_id)

    # If updating author_id, ensure the new author exists
    if payload.author_id is not None and payload.author_id != book.author_id:
        _ensure_author_exists(db, payload.author_id)
        book.author_id = payload.author_id

    # If updating ISBN, ensure unique vs others
    if payload.isbn and payload.isbn.strip().lower() != book.isbn.lower():
        conflict = db.execute(
            select(models.Book).where(func.lower(models.Book.isbn) == func.lower(payload.isbn.strip()))
        ).scalar_one_or_none()
        if conflict:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ISBN already exists")
        book.isbn = payload.isbn.strip()

    if payload.title is not None:
        book.title = payload.title.strip()
    if payload.publication_year is not None:
        book.publication_year = payload.publication_year
    if payload.available_copies is not None:
        book.available_copies = payload.available_copies

    db.add(book)
    db.commit()
    db.refresh(book)
    return book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = _get_book_or_404(db, book_id)
    db.delete(book)
    db.commit()
    return None
