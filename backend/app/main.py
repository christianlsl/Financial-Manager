from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .routers import auth, purchases, sales, companies, types


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (none for now)

app = FastAPI(title="Financial Manager API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust this to your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-New-Token"],
)


# Removed deprecated on_event startup in favor of lifespan


@app.get("/", tags=["health"])
def root():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
app.include_router(sales.router, prefix="/sales", tags=["sales"])
app.include_router(companies.router, prefix="/companies", tags=["companies"])
app.include_router(types.router, prefix="/types", tags=["types"])

