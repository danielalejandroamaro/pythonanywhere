from fastapi import APIRouter, Depends

from database import rows2dict, orm_query
from security.access import get_current_user

admin_routes = APIRouter(
    prefix="/admin",
    dependencies=[Depends(get_current_user)]
)

from models import QR


@admin_routes.get('/qr')
def get_qr():
    return {
        "items": rows2dict(
            orm_query(
                QR,
                True
            )
        )
    }


@admin_routes.post('/qr')
def create_qr():
    pass
