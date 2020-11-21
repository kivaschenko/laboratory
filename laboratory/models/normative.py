from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON
)
from .meta import Base


class Normative(Base):
    __tablename__ = 'normative'
    id = Column(Integer, primary_key=True)
    name = Column(String())
    data = Column(JSON)

    def __repr__(self):
        return f'<Normative(id={self.if} {self.name} data: {self.data})>'
