from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON
)
from .meta import Base

class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    substances = Column(JSON)
    solutions = Column(JSON)

    def __repr__(self):
        return f'<Recipe({self.name})>'

