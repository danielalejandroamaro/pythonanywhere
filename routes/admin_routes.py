from fastapi import APIRouter, Depends, Request

from database import orm_query, row2dict, orm_update_create, orm_delete
from security.access import get_current_user
from tools.fatapi_tools import export_xlsx, send_telegram_xlsx
from tools.sql_tools import Query
from tools.types import generar_cadena_aleatoria
from tools import r_params

admin_routes = APIRouter(
    prefix="/admin",
    dependencies=[Depends(get_current_user)]
)

from models import QR, Product, QueueProcess, Queue, Car, Persone


@admin_routes.get('/qr')
def get_qr():
    return {
        "items": Query(
            QR.__tablename__,
            params={
                r_params.NESTED: [Queue.__tablename__]
            }
        ).run()
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


@admin_routes.post("/queue_process")
async def create_queue_process(
        request: Request
):
    obj = await request.json()

    q = QueueProcess(
        **obj
    )
    orm_update_create(
        q,
        now=True
    )

    return {
        "items": [row2dict(q)]
    }


from typing import Optional


@admin_routes.get("/queue_process")
async def get_queue_process(
        queue_process_id: Optional[int] = None
):
    _fitler = {} if queue_process_id is None else {
        "id": queue_process_id
    }
    r = Query(
        QueueProcess.__tablename__,
        filters=_fitler,
        params={
            r_params.EXTEND: [
                f'{QueueProcess.product_id.key}.{Product.name.key}'
            ]
        }
    ).run()

    return {
        "items": r
    } if queue_process_id is None else r[0]


import pandas as pd


@admin_routes.get("/download_queue")
async def download_queue(
        qr_id: Optional[int] = None
):
    assert qr_id is not None, "debes pasar el qr_id"

    r = Query(
        Queue.__tablename__,
        filters={
            Queue.qr_id.key: qr_id
        },
        params={
            r_params.EXTEND: [
                f'{Queue.product_id.key}.{Product.name.key}',
                f'{Queue.car_id.key}.{Car.chapa.key}',
                f'{Queue.persone_id.key}.{Persone.name.key}',
            ]
        }
    ).run()
    matrix = pd.DataFrame(
        r
    )
    matrix.drop(
        columns=[
            Queue.product_id.key,
            Queue.id.key,
            Queue.car_id.key,
            Queue.persone_id.key,
            Queue.qr_id.key,
        ],
        inplace=True
    )

    matrix[
        Queue.is_done.key
    ] = [
        "si" if v else "no"
        for v in
        matrix[Queue.is_done.key].values
    ]

    matrix.rename(
        {
            f'{Queue.is_done.key}': 'ya cogió',
            f'{Queue.created_at.key}': 'entro en la cola',
            f'{Queue.product_id.key}.{Product.name.key}': 'producto',
            f'{Queue.car_id.key}.{Car.chapa.key}': 'chapa',
            f'{Queue.persone_id.key}.{Persone.name.key}': 'nombre',
        },
        axis=1,
        inplace=True
    )
    await send_telegram_xlsx(
        matrix,
        "cola"
    )
    return export_xlsx(
        matrix,
        "cola"
    )


@admin_routes.delete("/queue_process")
def delete_queue_process(queue_process_id: int):
    return {
        "items": orm_delete(
            QueueProcess,
            QueueProcess.id == queue_process_id
        )
    }
