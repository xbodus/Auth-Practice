"""Application Middleware"""
from .app import app
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware


app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost"]
)

app.add_middleware(
    CORSMiddleware,
    allowed_host=["http://localhost:5173"],
    allow_credentials=True,
)