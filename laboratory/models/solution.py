from datetime import date
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
    __tablename__ = 'solution'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    normative_id = Column(Integer)
    amount = Column(Numeric)
    created_at = Column(Date)
    due_date = Column(Date)

    def __repr__(self):
        return f'<Solution(id={self.id} {self.name} amount={self.amount} ml \
created at: {self.created_at})>'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_at = date.today()
