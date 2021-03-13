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
    __tablename__ = 'normatives'
    id = Column(Integer, primary_key=True)
    type = Column(String(20))
    name = Column(String(255), unique=True)
    output = Column(Numeric)
    data = Column(JSON)
    solutions = Column(JSON)
    as_subst = Column(Boolean)
    def __repr__(self):
        return f'<Normative(id={self.id}, {self.name}, output: {self.output}, \
data: {self.data})>'
