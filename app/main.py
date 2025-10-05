from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routers import authors, books, ai
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Library API")

# ✅ Add this CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)


app.include_router(authors.router)
app.include_router(books.router)   
app.include_router(ai.router)

@app.get("/")
def healthcheck():
    return {"status": "ok", "part": "B", "message": "authors endpoints ready"}
