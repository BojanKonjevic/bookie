from fastapi import FastAPI

from bookie.routes.auth import router as auth_router
from bookie.routes.bookmarks import router as bookmarks_router
from bookie.routes.tags import router as tags_router

from .database import lifespan

app = FastAPI(lifespan=lifespan)
app.include_router(bookmarks_router)
app.include_router(tags_router)
app.include_router(auth_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}
