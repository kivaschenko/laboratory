from datetime import date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date
)
from .meta import Base


class Substance(Base):
    __tablename__ = 'substance'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    measurement = Column(String(10), nullable=False)
    precursor = Boolean()
    description = Text()

    def __repr__(self):
        return f'<Substance(id={self.id} {self.name} measurement: \
{self.measurement} is precursor?: {self.precursor})>'


class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    substance_id = Column(Integer)
    amount = Column(Numeric)
    price = Column(Numeric)
    date = Column(Date)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_at = date.today()