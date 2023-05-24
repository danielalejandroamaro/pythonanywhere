from fastapi import FastAPI, Request, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME, is_debug

myapp = FastAPI()


def validation_exception_handler(request: Request, exc: HTTPException):
    exc = exc.args[0] if isinstance(exc.args[0], HTTPException) else exc
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"detail": exc.detail}),
        headers=exc.headers
    )


def create_app(*router_apis):
    new_app = FastAPI()

    from starlette.middleware.authentication import AuthenticationMiddleware
    from security.access import BearerAuthBackend

    new_app.add_middleware(
        AuthenticationMiddleware,
        backend=BearerAuthBackend(),
        on_error=validation_exception_handler
    )

    origins = [
        "http://localhost.tiangolo.com",
        "https://localhost.tiangolo.com",
        "http://localhost",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    new_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if not is_debug:
        prod_app = APIRouter(prefix=APP_NAME)
        new_app.include_router(prod_app)
        new_app = prod_app

    for _app in router_apis:
        new_app.include_router(_app)

    return new_app


from routes import v1 as basic_routes
from routes.admin_routes import admin_routes
from security.api_version import v1 as security_rutes

app = create_app(
    security_rutes,
    basic_routes,
    admin_routes,
)
