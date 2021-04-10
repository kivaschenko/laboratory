from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    DateTime,
    Text
)
from .meta import Base


class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    substance_name = Column(String(255), nullable=False)
    measurement = Column(String(10), nullable=False)
    amount = Column(Numeric, nullable=False)
    remainder = Column(Numeric)
    price = Column(Numeric, nullable=False)
    total_cost = Column(Numeric, nullable=False)
    creation_date = Column(DateTime)
    notes = Column(Text, nullable=True)
    normative = Column(String(255), nullable=True)
    recipe = Column(String(255), nullable=True)

    def __repr__(self):
        return f'<Stock(id={self.id} {self.substance_name} \
amount: {self.amount} price: {self.price} {self.creation_date})>'

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.creation_date = datetime.today()
