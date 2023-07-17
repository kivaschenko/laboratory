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
    amount = Column(Numeric)
    remainder = Column(Numeric)
    price = Column(Numeric)
    total_cost = Column(Numeric)
    created_at = Column(Date)
    due_date = Column(Date)
    notes = Column(Text)
    recipe = Column(String(255), nullable=True)
    def __repr__(self):
        return f'<Solution(id={self.id} {self.normative} amount={self.amount} {self.created_at})>'
