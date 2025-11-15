from app.main import app


if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run("app.main:app", host=settings.SERVER_HOST, port=settings.SERVER_PORT, reload=True)