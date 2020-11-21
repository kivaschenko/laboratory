from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    JSON
)
from .meta import Base


class Normative(Base):
    __tablename__ = 'normative'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    data = Column(JSON)
    output = Column(Numeric)

    def __repr__(self):
        return f'<Normative(id={self.if}, {self.name}, outut: {self.output}, \
data: {self.data})>'
