from fastapi import APIRouter, Depends

from database import rows2dict, orm_query, row2dict, orm_update_create
from security.access import get_current_user
from tools.types import generar_cadena_aleatoria

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
    new_qr = QR(
        code=generar_cadena_aleatoria()
    )
    orm_update_create(
        new_qr, now=True
    )
    return {
        "items": [
            row2dict(new_qr)
        ]
    }
