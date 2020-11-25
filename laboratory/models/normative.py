from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    JSON,
    Boolean
)
from .meta import Base


class Normative(Base):
    __tablename__ = 'normative'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    data = Column(JSON)
    output = Column(Integer)

    def __repr__(self):
        return f'<Normative(id={self.id}, {self.name}, output: {self.output}, \
data: {self.data})>'
