from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Text,
    Date
)
from .meta import Base


class Solution(Base):
    __tablename__ = 'solutions'
    id = Column(Integer, primary_key=True)
    normative = Column(String(255))
    measurement = Column(String)
    amount = Column(Numeric(8,3))
    remainder = Column(Numeric(11,3))
    price = Column(Numeric(8,2))
    total_cost = Column(Numeric(10,2))
    created_at = Column(Date)
    due_date = Column(Date)
    notes = Column(Text)

    def __repr__(self):
        return f'<Solution(id={self.id} {self.normative} amount={self.amount} \
ml created at: {self.created_at})>'
