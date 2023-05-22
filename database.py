from sqlalchemy.orm import Session

from engine import set_session, engine, metadata_obj
from tools.types import (
    check_collection
)


class NotFoundError(Exception):
    pass


def get_table(table_name):
    if table_name in engine.table_names():
        return Table(
            table_name,
            metadata_obj,
            autoload_with=engine
        )
    return None


@set_session
def orm_query(
        table,
        *filters,
        get_first=False,
        relationship=None,
        raise_on_not_found=False,
        session: Session = None
):
    if relationship is None:
        relationship = []
    elif check_collection(relationship):
        pass
    else:
        relationship = [relationship]

    query = session.query(table)

    if relationship:
        query = query.join(*relationship)

    query = query.filter(*filters)

    if get_first:
        f = query.first()
        if f is None and raise_on_not_found:
            raise NotFoundError()
        return f
    r = [*query.all()]
    if len(r) == 0 and raise_on_not_found:
        raise NotFoundError()
    return r


@set_session
def orm_update(table, value, *filters, _first=False, session: Session = None):
    stmt = (
        update(table)
        .where(*filters)
        .values(value)
        .returning(table)
        .execution_options(synchronize_session=False)
    )
    return r.first() if (r := session.execute(stmt)) and _first else [*r]


@set_session
def orm_delete(table, *filters, session: Session = None):
    stmt = (
        delete(table)
        .where(*filters)
        .returning(table)
        .execution_options(synchronize_session=False)
    )
    return [*session.execute(stmt)]


def row2dict(row, key=None):
    if row is None:
        return row
    key = [
        col.name for col in row.__table__.columns
    ] if key is None else key
    return {col: getattr(row, col) for col in key}


def rows2dict(rows, key=None):
    return [row2dict(row, key) for row in rows]


@set_session
def addTo_session(*objs: object, now=False, session: Session = None):
    if now:
        session.add_all(objs)
        session.commit()
        for item in objs:
            session.refresh(item)
        return session.flush()
    else:
        session.add_all(objs)


def orm_update_create(*obj, now=False, _safe=False):
    try:
        return addTo_session(*obj, now=now)
    except IntegrityError as err:
        if _safe:
            pass
        else:
            raise err
