from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    JSON,
)
from .meta import Base


class Normative(Base):
    __tablename__ = 'normatives'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    output = Column(Numeric)
    data = Column(JSON)
    def __repr__(self):
        return f'<Normative(id={self.id}, {self.name}, output: {self.output}, \
data: {self.data})>'
