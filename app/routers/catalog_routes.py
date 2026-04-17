from fastapi import APIRouter, UploadFile, File
from app.services.catalog_service import update_catalog, get_catalog

router = APIRouter()


@router.post("/update")
def update(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8")
    return update_catalog(content)


@router.get("/")
def catalog():
    return get_catalog()
