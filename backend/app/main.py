from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from . import db
from .core.config import settings
from .routers import auth, purchases, sales, companies, types, customers, suppliers, departments, statistics


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.Base.metadata.create_all(bind=db.engine)
    yield


app = FastAPI(title="Financial Manager API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-New-Token"],
)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok"}


@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
app.include_router(sales.router, prefix="/sales", tags=["sales"])
app.include_router(companies.router, prefix="/companies", tags=["companies"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
app.include_router(departments.router, prefix="/departments", tags=["departments"])
app.include_router(types.router, prefix="/types", tags=["types"])
app.include_router(statistics.router, prefix="/statistics", tags=["statistics"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.SERVER_HOST, port=settings.SERVER_PORT, reload=True)