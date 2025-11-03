"""
Plot class representing a business opportunity in the game.
"""

import json
from enum import Enum
from typing import Optional
from pathlib import Path
from ledger import Ledger
from event import Event


class SolvencyState(Enum):
    """Solvency states for a Plot."""
    UNDERWATER = "Underwater"
    PAYING_INVESTORS = "Paying Investors"
    PAYING_PROFIT = "Paying Profit"


class Plot(Event):
    """
    A Plot represents a business opportunity with investment mechanics.
    
    Class Attributes:
        DATA_DIRECTORY: Name of the subdirectory containing plot JSON files
    
    Attributes:
        story: A unique, fun, short story of a business opportunity (business plan)
        cost: Cost in Credits (ranges from low thousands to high hundreds of thousands)
        conversion_ratio: Conversion ratio from Credits to Investor Points
                         (e.g., 1000 means "1000 Credits is 1 Investor Point")
        ledger: Ledger instance tracking financial state and player investments
        solvency_state: Current solvency state (initialized as Underwater)
        hurdle_rate: Hurdle rate representing the cost of risk (0.0 to 0.10, i.e., 0% to 10%)
    """
    
    DATA_DIRECTORY = "Plots"
    
    def __init__(
        self,
        filename: Optional[str] = None,
        story: Optional[str] = None,
        cost: Optional[int] = None,
        conversion_ratio: Optional[int] = None,
        hurdle_rate: float = 0.0,
        date_started: Optional[str] = None,
        account: Optional[str] = None,
        product_name: Optional[str] = None,
        url: Optional[str] = None
    ):
        """
        Initialize a Plot.
        
        Can be initialized from a JSON file or by providing individual parameters.
        If filename is provided, it loads from that file. Otherwise, uses provided parameters.
        
        Args:
            filename: Path to JSON file to load from (optional)
            story: Business opportunity description (required if filename not provided)
            cost: Cost in Credits (required if filename not provided)
            conversion_ratio: Credits per Investor Point (required if filename not provided)
            hurdle_rate: Risk hurdle rate (0.0 to 0.10, default 0.0)
            date_started: Date started in ISO 8601 format (optional)
            account: Account string identifier (optional)
            product_name: Product name string (optional)
            url: URL to Google Drive folder (optional)
        """
        if filename:
            # Load from JSON file
            self._load_from_file(filename)
        else:
            # Initialize from parameters
            if story is None or cost is None or conversion_ratio is None:
                raise ValueError("Either filename must be provided, or story, cost, and conversion_ratio must be provided")
            
            self.story = story
            self.cost = cost
            self.conversion_ratio = conversion_ratio
            self.hurdle_rate = hurdle_rate
            
            # Metadata from JSON
            self.date_started = date_started
            super().__init__(event_date=date_started)
            self.account = account
            self.product_name = product_name
            self.url = url
        
        # The Ledger
        self.ledger = Ledger()
        
        # Solvency State
        self.solvency_state = SolvencyState.UNDERWATER
    
    def _load_from_file(self, filename: str):
        """
        Load plot data from a JSON file.
        
        Args:
            filename: Path to JSON file
        """
        file_path = Path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Plot file not found: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract required fields
            self.story = data.get("description", "")
            self.cost = data.get("cost", 0)
            self.conversion_ratio = data.get("conversion_ratio", 1000)
            self.hurdle_rate = data.get("hurdle_rate", 0.0)
            self.date_started = data.get("date_started", None)
            super().__init__(event_date=self.date_started)
            self.account = data.get("account", None)
            self.product_name = data.get("product_name", None)
            self.url = data.get("url", None)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON in {filename}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading plot from {filename}: {e}")
    
    def __repr__(self):
        return (
            f"Plot(story='{self.story[:50]}...', cost={self.cost}, "
            f"conversion_ratio={self.conversion_ratio}, "
            f"solvency_state={self.solvency_state.value}, "
            f"hurdle_rate={self.hurdle_rate:.1%})"
        )

