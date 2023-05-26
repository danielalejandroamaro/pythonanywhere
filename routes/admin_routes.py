from fastapi import APIRouter, Depends, Request

from database import rows2dict, orm_query, row2dict, orm_update_create, orm_delete
from security.access import get_current_user
from tools.types import generar_cadena_aleatoria

admin_routes = APIRouter(
    prefix="/admin",
    dependencies=[Depends(get_current_user)]
)

from models import QR, Product


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


@admin_routes.post("/products")
async def create_products(
        request: Request
):
    obj = await request.json()

    name = obj.get("name", None)

    assert name is not None and len(name) > 0, "no se puede agrear un producto con ese nombre"
    q = orm_query(
        Product,
        Product.name == name,
        get_first=True
    )
    assert q is None, "no se puede crear dos productos con el mismo nombre"
    if q is None:
        q = Product(
            name=name
        )
        orm_update_create(
            q,
            now=True
        )

    return {
        "items": [row2dict(q)]
    }


@admin_routes.delete("/products")
def delete_products(product_id: int):
    return {
        "items": orm_delete(
            Product,
            Product.id == product_id
        )
    }
