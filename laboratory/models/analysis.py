from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    JSON
)
from .meta import Base

class Analysis(Base):
    __tablename__ = 'analysis'
    id = Column(Integer, primary_key=True)
    recipe_name = Column(String(255))
    quantity = Column(Integer)
    done_date = Column(Date)
    total_cost = Column(Integer)
    substances_cost = Column(JSON)
    solutions_cost = Column(JSON)

    def __repr__(self):
        return f'<Analysis({self.id} - {self.recipe_name} - {self.quantity} - {self.done_date})>'
