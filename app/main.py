from fastapi import FastAPI
from app.routers.catalog_routes import router as catalog_router
from app.routers.payment_routes import router as payment_router

app = FastAPI(
    title="Bank Payment Service",
    version="1.0.0"
)

# Prefix /catalog
app.include_router(catalog_router, prefix="/catalog", tags=["Catalogo"])

# Prefix /payment
app.include_router(payment_router, prefix="/payment", tags=["Pagos"])


@app.get("/")
def root():
    return {
        "message": "Digital Bank Payment Service API",
        "docs": "/docs"
    }
