from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    JSON, 
    Date
)
from .meta import Base


class Solution(Base):
    __tablename__ = 'solutions'
    id = Column(Integer, primary_key=True)
    normative = Column(String(255))
    amount = Column(Numeric)
    created_at = Column(Date)
    due_date = Column(Date)
    user_id = Column(Integer)

    def __repr__(self):
        return f'<Solution(id={self.id} {self.normative} amount={self.amount} \
ml created at: {self.created_at})>'

