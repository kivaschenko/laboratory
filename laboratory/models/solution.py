"""Solution model for laboratory management system."""

from sqlalchemy import Column, Integer, Numeric, String, Text, Date
from .meta import Base


class Solution(Base):
    """
    Model representing a prepared solution in the laboratory.

    Solutions are prepared according to normative recipes and used in
    various analyses. Each solution has quantity tracking, cost calculation,
    and expiration management.

    Attributes:
        id (int): Primary key, auto-generated
        normative (str): Name of the normative recipe used
        measurement (str): Unit of measurement (e.g., 'мл', 'л')
        amount (Numeric): Total amount prepared
        remainder (Numeric): Remaining amount available
        price (Numeric): Price per unit
        total_cost (Numeric): Total cost of preparation
        created_at (Date): Date when solution was prepared
        due_date (Date): Expiration date
        notes (Text): Additional notes and preparation details
        recipe (str): Associated analysis recipe name (optional)

    Example:
        >>> solution = Solution(
        ...     normative='HCl 0.1M',
        ...     amount=1000,
        ...     measurement='мл',
        ...     price=0.05
        ... )
    """

    __tablename__ = "solutions"

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

    def __repr__(self) -> str:
        """Return string representation of the solution."""
        return (
            f'<Solution(id={self.id}, normative="{self.normative}", '
            f"amount={self.amount}, created_at={self.created_at})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if solution has expired."""
        if not self.due_date:
            return False
        from datetime import date

        return date.today() > self.due_date

    @property
    def usage_percentage(self) -> float:
        """Calculate percentage of solution used."""
        if not self.amount or self.amount == 0:
            return 0.0
        return float((self.amount - (self.remainder or 0)) / self.amount * 100)
