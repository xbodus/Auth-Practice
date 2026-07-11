from .app import app


@app.get("/")
async def index():
    return {"message": "Hello World!"}
