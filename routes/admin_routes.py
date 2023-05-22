from fastapi import APIRouter, Depends

from security.access import get_current_user

admin_routes = APIRouter(
    prefix="/admin",
    dependencies=[Depends(get_current_user)]
)


@admin_routes.get('/qr')
def get_qr():
    pass


@admin_routes.post('/qr')
def create_qr():
    pass
