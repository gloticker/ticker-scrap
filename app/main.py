from fastapi import FastAPI
from .api.routes import stock_routes

app = FastAPI(
    title="ticker API",
    description="current ticker data API",
    version="1.0.0"
)

app.include_router(stock_routes.router, prefix="/stocks", tags=["stocks"])


@app.get("/")
async def root():
    return {"message": "ticker scrap server"}
