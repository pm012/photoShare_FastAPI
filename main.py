import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware  # Використовуємо правильну мідлварь
from fastapi.responses import PlainTextResponse 

from src.routes import auth, photos, transformations, comments, users, ratings, search
from src.conf.config import settings
from src.services.limiter import limiter

app = FastAPI(
    title="PhotoShare API",
    description="REST API застосунок - аналог Instagram (FastAPI, SQLAlchemy, Alembic)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.FRONTEND_URL.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Налаштовуємо лімітер всередині FastAPI state
app.state.limiter = limiter

# Підключаємо офіційну мідлварь від slowapi
app.add_middleware(SlowAPIMiddleware)

# Обробник помилки, коли користувач робить забагато запитів
@app.exception_handler(RateLimitExceeded)
def _rate_limit_exceeded_handler(request, exc):
    return PlainTextResponse(
        "Too many requests. Please try again later.", 
        status_code=429
    )

# Підключаємо роутери
app.include_router(auth.router, prefix="/api")
app.include_router(photos.router, prefix="/api")
app.include_router(transformations.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(ratings.router, prefix="/api")
app.include_router(search.router, prefix="/api")

@app.get("/", tags=["root"])
def root():
    return {"message": "Welcome to PhotoShare (PhotoShare REST API)"}


@app.get("/health", tags=["root"])
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
