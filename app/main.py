from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, upload, generate, styles
from app.core.config import get_settings
from app.core.database import Base, engine, run_simple_migrations


settings = get_settings()

app = FastAPI(title=settings.APP_NAME)


origins = [
    origin.strip()
    for origin in settings.BACKEND_CORS_ORIGINS.split(",")
    if origin.strip()
]

# Для полного открытия CORS ставим "*" и отключаем credentials,
# т.к. wildcard нельзя использовать с allow_credentials=True
allow_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


run_simple_migrations()
Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(styles.router)


