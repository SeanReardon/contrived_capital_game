"""
Ledger class representing the accounting ledger for a Plot.
"""

from typing import Dict


class Ledger:
    """
    A Ledger tracks the financial state and player investments for a Plot.
    
    Attributes:
        balance: Sum balance in the ledger, initialized to 0
        investor_points: Dict mapping player names to their Investor Points
        hurdle: Total investor points × conversion ratio (Credits owed to investors)
        carry_points: Dict mapping player names to their Carry Points
        paid_out_profit_total: Cumulative profit distributed (for tracking)
    """
    
    def __init__(self):
        """Initialize an empty Ledger."""
        self.balance = 0
        self.investor_points: Dict[str, int] = {}  # player_name -> points
        self.hurdle = 0  # Will be calculated as total_investor_points × conversion_ratio
        self.carry_points: Dict[str, int] = {}  # player_name -> points
        self.paid_out_profit_total = 0
    
    def add_investor_points(self, player_name: str, points: int, conversion_ratio: int):
        """
        Add Investor Points for a player and recalculate the hurdle.
        
        The hurdle is the total Investor Points × conversion ratio, representing
        the Credits owed to all investors.
        
        Args:
            player_name: Name of the player
            points: Number of Investor Points to add (can be negative to remove)
            conversion_ratio: The conversion ratio for this Plot
        """
        if player_name not in self.investor_points:
            self.investor_points[player_name] = 0
        
        self.investor_points[player_name] += points
        
        # Don't allow negative investor points
        if self.investor_points[player_name] < 0:
            self.investor_points[player_name] = 0
        
        # Recalculate hurdle based on total investor points
        self.hurdle = self.get_total_investor_points() * conversion_ratio
    
    def add_carry_points(self, player_name: str, points: int):
        """
        Add Carry Points for a player.
        
        Args:
            player_name: Name of the player
            points: Number of Carry Points to add (can be negative to remove)
        """
        if player_name not in self.carry_points:
            self.carry_points[player_name] = 0
        
        self.carry_points[player_name] += points
        
        # Don't allow negative carry points
        if self.carry_points[player_name] < 0:
            self.carry_points[player_name] = 0
    
    def get_total_investor_points(self) -> int:
        """
        Calculate the total Investor Points across all players.
        
        Returns:
            Sum of all Investor Points
        """
        return sum(self.investor_points.values())
    
    def get_total_carry_points(self) -> int:
        """
        Calculate the total Carry Points across all players.
        
        Returns:
            Sum of all Carry Points
        """
        return sum(self.carry_points.values())
    
    def __repr__(self):
        return (
            f"Ledger(balance={self.balance}, "
            f"investor_points={self.get_total_investor_points()}, "
            f"hurdle={self.hurdle}, "
            f"carry_points={self.get_total_carry_points()}, "
            f"paid_out_profit={self.paid_out_profit_total})"
        )

