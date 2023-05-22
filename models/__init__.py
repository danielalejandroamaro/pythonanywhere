from sqlalchemy import String, Column, Integer, DateTime, func, ForeignKey
from sqlalchemy import text
from engine import Base


class Persone(Base):
    __tablename__ = "person"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=True)
    telefono = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)


class Car(Base):
    __tablename__ = "car"
    id = Column(Integer, primary_key=True)
    chapa = Column(String(20), nullable=True)


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=True)


class Queue(Base):
    __tablename__ = "queue"
    id = Column(Integer, primary_key=True)
    index = Column(Integer, nullable=False)

    cupet = Column(String(255), nullable=False)

    persone_id = Column(Integer, ForeignKey(Persone.id), nullable=False)
    car_id = Column(Integer, ForeignKey(Car.id), nullable=False)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)

    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)


class QR(Base):
    __tablename__ = "qr_table"
    id = Column(Integer, primary_key=True)
    code = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    count = Column(Integer, nullable=False, server_default=text("0"))
