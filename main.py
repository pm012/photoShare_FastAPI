import uvicorn
from fastapi import FastAPI
from src.routes import auth, photos, transformations, comments, users

app = FastAPI(
    title="PhotoShare API",
    description="REST API застосунок - аналог Instagram (FastAPI, SQLAlchemy, Alembic)",
    version="1.0.0"
)

app.include_router(auth.router, prefix="/api")
app.include_router(photos.router, prefix="/api")
app.include_router(transformations.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(users.router, prefix="/api")   

@app.get("/", tags=["root"])
def root():
    return {"message": "Welcome to PhotoShare (PhotoShare REST API)"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
