from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, upload, generate, styles
from app.core.config import get_settings
from app.core.database import Base, engine


settings = get_settings()

app = FastAPI(title=settings.APP_NAME)


origins = [
    origin.strip()
    for origin in settings.BACKEND_CORS_ORIGINS.split(",")
    if origin.strip()
]

# Allow all origins if "*" is set or if no specific origins provided
if settings.BACKEND_CORS_ORIGINS == "*" or not origins:
    allow_origins = ["*"]
else:
    allow_origins = origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(styles.router)


