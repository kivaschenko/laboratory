from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    DateTime
)
from .meta import Base


class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    substance_id = Column(Integer, nullable=False)
    substance_name = Column(String(255))
    measurement = Column(String(10), nullable=False)
    amount = Column(Numeric, nullable=False)
    price = Column(Numeric, nullable=False)
    date = Column(DateTime)

    def __repr__(self):
        return f'<Stock(id={self.id} {self.substance_name} amount: \
{self.amount} {self.measurement} price: {self.price} UAH from {self.date})>'