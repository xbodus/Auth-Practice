from fastapi import FastAPI
from .api import router
from .middleware import setup_middleware
app = FastAPI()
app.include_router(router)
setup_middleware(app)