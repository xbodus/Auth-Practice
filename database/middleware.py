"""Application Middleware"""
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware



def setup_middleware(app):
    hosts = [
        "localhost",
        "127.0.0.1"
    ]
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=hosts
    )

    origins = [
        "http://localhost:5173",
        "http://localhost:8000"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )