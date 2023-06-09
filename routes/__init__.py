from io import BytesIO
from typing import Optional

import qrcode
from fastapi import Request, APIRouter, status, HTTPException
from fastapi.responses import StreamingResponse

from database import orm_query, orm_update_create, rows2dict
from models import Persone, Car, Product, Queue, QR
from tools.sql_tools import Query
from tools import r_params

v1 = APIRouter()
_database = {
    "code": 0,
    "lista": []
}


@v1.get("/get_next_code")
def root():
    _next = _database.get("code") + 1
    _database.update(
        code=_next
    )
    return {"next_code": _next}


@v1.get("/products")
def products():
    return {
        "items": rows2dict(
            orm_query(
                Product,
                True
            )
        )
    }


@v1.get("/queue")
def get_queue(
        index__lt: Optional[int] = None,
        index__gt: Optional[int] = None,
        product_id: Optional[int] = None,
        chapa: Optional[str] = None
):
    _filter = {
        Queue.is_done.key: False
    }
    _complex_fitler = {}
    if product_id is not None:
        _filter.update(product_id=product_id)
    if index__lt is not None:
        _filter.update(index__lt=index__lt)
    if index__gt is not None:
        _filter.update(index__gt=index__gt)
    if chapa is not None:
        _complex_fitler.update(
            **{
                Queue.car_id.key: {
                    Car.chapa.key: chapa
                }
            }
        )

    items = Query(
        Queue.__tablename__,
        filters=_filter,
        complex_filters=_complex_fitler,
        params={
            r_params.EXTEND: [
                f'{Queue.product_id.key}.{Product.name.key}',
                f'{Queue.persone_id.key}.{Persone.name.key}',
                f'{Queue.car_id.key}.{Car.chapa.key}'
            ]
        }
    ).run()

    return {
        "items": items
    }


@v1.get("/find")
def find(
        chapa: str
):
    chapa = "".join(chapa.upper().split(' '))

    q = Query(
        Queue.__tablename__,
        complex_filters={
            Queue.car_id.key: {
                Car.chapa.key: chapa
            }
        },
        params={
            r_params.ORDERBY: [
                f'-{Queue.created_at.key}'
            ],
            r_params.EXTEND: [
                f'{Queue.persone_id.key}.{Persone.name.key}',
                f'{Queue.car_id.key}.{Car.chapa.key}',
                f'{Queue.product_id.key}.{Product.name.key}'
            ]
        }
    ).run()

    return {
        "items": q
    }


@v1.get("/products")
def root():
    list = _database.get("lista")
    return {"list": list}


class ValidationException(Exception):

    def __init__(self, function):
        self.function = function

    @staticmethod
    def validate(self, *args, **kwargs):
        return self.function(*args, **kwargs)


@v1.post("/queue")
async def root(request: Request):
    obj = await request.json()
    qr_code = obj.get("qr_code")

    qr_obj = orm_query(
        QR,
        QR.code == qr_code,
        get_first=True,
        raise_on_not_found=True
    )

    anotated = orm_query(
        Queue,
        Queue.qr_id == qr_obj.id
    )
    if not (len(anotated) < 250):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "push_notification": "Esta cola esta llena, espere un nuevo QR"
            }
        )

    name = obj.get(Persone.name.key, "") or ""
    telefono = obj.get(Persone.telefono.key, "") or ""
    product_id = obj.get(Queue.product_id.key, []) or []

    if not (len(product_id) > 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "push_notification": "Tiene que tener al menos un producto seleccionado"
            }
        )

    chapa: str = obj.get(Car.chapa.key, "")
    chapa = "".join(chapa.upper().split(' '))

    if not chapa.isalnum() or len(chapa) != 7 or not chapa[0].isalpha() or not chapa[1:].isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "push_notification": 'La chapa del carro debe tener una letra seguida de 6 dígitos'
            }
        )

    q = Query(
        Queue.__tablename__,
        filters={
            Queue.product_id.key: product_id
        },
        complex_filters={
            Queue.car_id.key: {
                Car.chapa.key: chapa
            },
            Queue.qr_id.key: {
                QR.code.key: qr_code
            }
        }, params={
            r_params.EXTEND: [
                Queue.car_id.key,
                Queue.qr_id.key
            ],
            r_params.GROUPBY: [
                Queue.product_id.key
            ]
        }, agg_filters={
            Queue.product_id.key: "count"  # func.count
        }
    ).run()
    q = {
        i[Queue.product_id.key]
        for i in q
    }

    product_id = [
        p_id
        for p_id
        in product_id
        if p_id not in q
    ]

    if not (len(product_id) > 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "push_notification": "Chapa ya registrada. No puede inscribirse en esta lista otra vez",
            }
        )

    _person: Persone = orm_query(
        Persone,
        Persone.telefono == telefono,
        Persone.name == name,
        get_first=True
    )

    if _person is None:
        _person = Persone(
            name=name,
            telefono=telefono
        )
        orm_update_create(
            _person,
            now=True
        )

    car = orm_query(
        Car,
        Car.chapa == chapa,
        get_first=True
    )
    if car is None:
        car = Car(chapa=chapa)
        orm_update_create(
            car,
            now=True
        )

    queue_product_max = Query(
        Queue.__tablename__,
        filters={
            Queue.qr_id.key: qr_obj.id
        },
        params={
            r_params.GROUPBY: [Queue.product_id.key]
        },
        agg_filters={
            Queue.index.key: "max"  # func.max
        }
    ).run()

    queue_product_max = {
        qp_max[Queue.product_id.key]: qp_max[f'{Queue.index.key}__max']
        for qp_max in queue_product_max
    }

    queues = [*map(
        lambda _product_id:
        Queue(
            cupet="Acapulco",
            persone_id=_person.id,
            car_id=car.id,
            product_id=_product_id,
            qr_id=qr_obj.id,
            index=queue_product_max.get(_product_id, 0) + 1
        ),
        product_id
    )]

    orm_update_create(
        *queues,
        now=True
    )

    data = {
        "items": Query(
            Queue.__tablename__,
            complex_filters={
                Queue.car_id.key: {
                    Car.chapa.key: chapa
                }
            },
            params={
                r_params.EXTEND: [
                    f'{Queue.car_id.key}.{Car.chapa.key}',
                    f'{Queue.persone_id.key}.{Persone.name.key}',
                    f'{Queue.product_id.key}.{Product.name.key}'
                ],
            }
        ).run()
    }

    return data


# @v1.post('/procesar_datos')
# def procesar_datos():
#     nombre = request.form['nombre']
#     ci = request.form['ci']
#     placa = request.form['placa']
#     telefono = request.form['telefono']
#
#     if len(nombre) > 40:
#         return 'El nombre no puede tener más de 40 caracteres'
#     if not ci.isdigit() or len(ci) not in {11, 6}:
#         return 'El carnet de identidad debe tener 11 caracteres numéricos'
#     if not placa.isalnum() or len(placa) != 7 or not placa[0].isalpha() or not placa[1:].isdigit():
#         return 'La placa del carro debe tener una letra seguida de 6 dígitos'
#     if not telefono.isdigit() or len(telefono) != 8:
#         return 'El número de teléfono debe tener 8 caracteres numéricos'
#
#     qr_text = f"Nombre: {nombre}\nCI: {ci}\nPlaca: {placa}\nTeléfono: {telefono}"
#
#     # Generar el código QR
#     qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
#     qr.add_data(qr_text)
#     qr.make(fit=True)
#
#     # Crear un objeto de BytesIO para guardar la imagen del código QR
#     img_buffer = BytesIO()
#     img = qr.make_image(fill_color="black", back_color="white")
#     img.save(img_buffer, format='png')
#     img_buffer.seek(0)
#
#     # Enviar la imagen del código QR como respuesta
#     return send_file(img_buffer, mimetype='image/png')


@v1.get('/get_qr')
def procesar_datos(code: str):
    # Generar el código QR
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(code)
    qr.make(fit=True)

    # Crear un objeto de BytesIO para guardar la imagen del código QR
    img_buffer = BytesIO()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(img_buffer, kind='png')
    img_buffer.seek(0)

    # Enviar la imagen del código QR como respuesta
    return StreamingResponse(img_buffer, media_type='image/png')
