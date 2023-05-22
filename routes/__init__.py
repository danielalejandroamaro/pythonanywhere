from typing import Optional

from fastapi import Request, APIRouter

from database import orm_query, orm_update_create, rows2dict
from models import Persone, Car, Product, Queue
from tools.sql_tools import Query
from tools.types import first
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
        product_id: int = 0,
):
    _filter = {
        "product_id": product_id
    }
    if index__lt is not None:
        _filter.update(index__lt=index__lt)
    if index__gt is not None:
        _filter.update(index__gt=index__gt)

    items = Query(
        Queue.__table__,
        filters=_filter,
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


@v1.get("/products")
def root():
    list = _database.get("lista")
    return {"list": list}


@v1.post("/add_to_stack")
async def root(request: Request):
    _list = _database.get("lista")
    obj = await request.json()

    name = obj.get(Persone.name.key, "")
    telefono = obj.get(Persone.telefono.key, "")
    product_id = obj.get(Queue.product_id.key, [])
    assert len(product_id) > 1, "tiene que tener al menos un producto seleccionado"

    chapa = obj.get(Car.chapa.key, "")

    person = orm_query(
        Persone,
        Persone.telefono == telefono
    )
    _person: Persone = None

    if len(person) > 0:
        _person = first(
            filter(
                lambda x: x.name == name,
                person
            ),
            raise_on_empty=False
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
        car = Car(
            chapa=chapa
        )
        orm_update_create(
            car,
            now=True
        )

    _max = 0
    q = orm_query(
        Queue,
        Queue.cupet == "Acapulco"
    )
    if len(q) > 0:
        _max = max(
            *map(
                lambda x: x.index
                , q
            )
        )
    queues = [*map(
        lambda _product_id:
        Queue(
            cupet="Acapulco",
            persone_id=_person.id,
            car_id=car.id,
            product_id=_product_id,
            index=_max + 1

        ),
        product_id
    )]

    orm_update_create(
        *queues,
        now=True
    )

    data = {
        "index": queues[0].index,
        "chapa": car.chapa
    }

    # await python_telegram_bot(data)
    return data


@v1.post('/procesar_datos')
def procesar_datos():
    nombre = request.form['nombre']
    ci = request.form['ci']
    placa = request.form['placa']
    telefono = request.form['telefono']

    if len(nombre) > 40:
        return 'El nombre no puede tener más de 40 caracteres'
    if not ci.isdigit() or len(ci) not in {11, 6}:
        return 'El carnet de identidad debe tener 11 caracteres numéricos'
    if not placa.isalnum() or len(placa) != 7 or not placa[0].isalpha() or not placa[1:].isdigit():
        return 'La placa del carro debe tener una letra seguida de 6 dígitos'
    if not telefono.isdigit() or len(telefono) != 8:
        return 'El número de teléfono debe tener 8 caracteres numéricos'

    qr_text = f"Nombre: {nombre}\nCI: {ci}\nPlaca: {placa}\nTeléfono: {telefono}"

    # Generar el código QR
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_text)
    qr.make(fit=True)

    # Crear un objeto de BytesIO para guardar la imagen del código QR
    img_buffer = BytesIO()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(img_buffer, format='png')
    img_buffer.seek(0)

    # Enviar la imagen del código QR como respuesta
    return send_file(img_buffer, mimetype='image/png')


