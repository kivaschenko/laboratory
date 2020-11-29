from sqlalchemy import (
    Column,
    Integer,
    String,
    Date
)
from .meta import Base

class Analysis(Base):
    __tablename__ = 'analysis'
    id = Column(Integer, primary_key=True)
    recipe_name = Column(String(255))
    done_date = Column(Date)

    def __repr__(self):
        return f'<Analysis({self.recipe_name} - {self.done_date})>'   