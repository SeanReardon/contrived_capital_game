"""
Game singleton class representing the state of play.
"""

from typing import List, Optional
from plot import Plot
from player import Player
from bank import Bank


class Game:
    """
    Game singleton that represents the state of play.
    
    Manages:
    - List of players
    - List of plots (10 plots on the table)
    - Bank instance with all bank transactions
    - Initial game setup
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only one Game instance."""
        if cls._instance is None:
            cls._instance = super(Game, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the game state."""
        # Only initialize once (singleton pattern)
        if hasattr(self, '_initialized'):
            return
        
        self.players: List[Player] = []
        self.plots: List[Plot] = []
        self.bank: Optional[Bank] = None
        self._initialized = True
    
    def setup(self, players: List[Player], plots: List[Plot]):
        """
        Set up the game with players and plots.
        
        Setup rules:
        - 10 Plots are placed on the table (face up, next to each other)
        - Each Plot gives each player a single Carry Point
        - Each Plot's Ledger is initialized to 0 (already done in Plot.__init__)
        - Each Plot's Solvency State is initialized to Underwater (already done in Plot.__init__)
        - Each player starts with 10 Investor Points in hand
        - Each player starts with 10 Carry Points in hand
        - Each player starts with 0 Credits
        
        Args:
            players: List of Player instances
            plots: List of 10 Plot instances to place on the table
        """
        # Set players
        self.players = players
        
        # Set up plots
        if len(plots) != 10:
            raise ValueError(f"Expected 10 plots, got {len(plots)}")
        
        self.plots = plots
        
        # Each Plot gives each player a single Carry Point
        # Add 1 Carry Point to each player's ledger for each plot
        for plot in self.plots:
            for player in self.players:
                plot.ledger.add_carry_points(player.name, 1)
    
    def __repr__(self):
        return (
            f"Game(players={len(self.players)}, plots={len(self.plots)})"
        )

