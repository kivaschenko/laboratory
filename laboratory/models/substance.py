from sqlalchemy import (
    Column,
    Integer,
    String
)
from .meta import Base


class Substance(Base):
    __tablename__ = 'substances'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    measurement = Column(String(10), nullable=False)
    def __repr__(self):
        return f'<Substance(id={self.id} {self.name} measurement: \
{self.measurement})>'
