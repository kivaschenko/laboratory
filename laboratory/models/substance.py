"""Substance model for laboratory management system."""

from sqlalchemy import Column, Integer, String
from .meta import Base


class Substance(Base):
    """
    Model representing a chemical substance used in laboratory operations.

    Substances are the basic building blocks for creating solutions and
    performing analyses. Each substance has a unique name and associated
    measurement unit.

    Attributes:
        id (int): Primary key, auto-generated
        name (str): Unique name of the substance (max 255 chars)
        measurement (str): Unit of measurement (e.g., 'г', 'мл', 'кг')

    Example:
        >>> substance = Substance(name='Sodium Chloride', measurement='г')
        >>> print(substance.name)
        'Sodium Chloride'
    """

    __tablename__ = "substances"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    measurement = Column(String(10), nullable=False)

    def __repr__(self) -> str:
        """Return string representation of the substance."""
        return f'<Substance(id={self.id}, name="{self.name}", measurement="{self.measurement}")>'

    def __str__(self) -> str:
        """Return human-readable string representation."""
        return f"{self.name} ({self.measurement})"
