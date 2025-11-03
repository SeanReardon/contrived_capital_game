"""
Move class representing a player action in the game.
"""

import json
from typing import Optional
from pathlib import Path
from datetime import datetime
from event import Event


class Move(Event):
    """
    A Move represents a player action in the game.
    
    Class Attributes:
        DATA_DIRECTORY: Name of the subdirectory containing move JSON files
    
    Attributes:
        filename: Original filename of the move (e.g., "2024-01-15-SeanReardon-Mamani.txt")
        date: Date of the move (YYYY-MM-DD format)
        user_name: Name of the user making the move (FirstLast format, no space)
        project: Name of the plot/project this move affects
        push_credits: Amount of credits for Push action (default 0)
        pull_credits: Amount of credits for Pull action (default 0)
        buy_in_credits: Amount of credits for Buy-In action (default 0)
        cash_out_credits: Amount of credits for Cash-Out action (default 0)
    """
    
    DATA_DIRECTORY = "Moves"
    
    def __init__(
        self,
        filename: Optional[str] = None,
        date: Optional[str] = None,
        user_name: Optional[str] = None,
        project: Optional[str] = None,
        push_credits: float = 0.0,
        pull_credits: float = 0.0,
        buy_in_credits: float = 0.0,
        cash_out_credits: float = 0.0
    ):
        """
        Initialize a Move.
        
        Can be initialized from a JSON file or by providing individual parameters.
        If filename is provided, it loads from that file. Otherwise, uses provided parameters.
        
        Args:
            filename: Path to JSON file to load from (optional)
            date: Date of the move in YYYY-MM-DD format (required if filename not provided)
            user_name: Name of the user making the move in FirstLast format (required if filename not provided)
            project: Name of the project this move affects (required if filename not provided)
            push_credits: Amount of credits for Push action (default 0)
            pull_credits: Amount of credits for Pull action (default 0)
            buy_in_credits: Amount of credits for Buy-In action (default 0)
            cash_out_credits: Amount of credits for Cash-Out action (default 0)
        """
        if filename:
            # Load from JSON file
            self._load_from_file(filename)
        else:
            # Initialize from parameters
            if date is None or user_name is None or project is None:
                raise ValueError("Either filename must be provided, or date, user_name, and project must be provided")
            
            self.filename = f"{date}-{user_name}-{project}.txt"
            self.date = date
            super().__init__(event_date=date)
            self.user_name = user_name
            self.project = project
            self.push_credits = push_credits
            self.pull_credits = pull_credits
            self.buy_in_credits = buy_in_credits
            self.cash_out_credits = cash_out_credits
    
    def _load_from_file(self, filename: str):
        """
        Load move data from a JSON file.
        
        The filename should be in the format YYYY-MM-DD-UserName-ProjectName.txt
        (e.g., 2024-01-15-SeanReardon-Mamani.txt)
        
        Args:
            filename: Path to JSON file
        """
        file_path = Path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Move file not found: {filename}")
        
        # Extract date, user_name, and project from filename
        # Format: YYYY-MM-DD-UserName-ProjectName.txt
        filename_stem = file_path.stem  # Remove .txt extension
        parts = filename_stem.split('-')
        
        if len(parts) < 3:
            raise ValueError(f"Invalid filename format: {filename}. Expected YYYY-MM-DD-UserName-ProjectName.txt")
        
        self.filename = file_path.name
        self.date = f"{parts[0]}-{parts[1]}-{parts[2]}"
        super().__init__(event_date=self.date)
        self.user_name = parts[3]
        # Everything after the date and user_name is the project name
        self.project = '-'.join(parts[4:]) if len(parts) > 4 else parts[3]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract action amounts from JSON
            # JSON structure example:
            # {"project": "Mamani", "Push": 100, "Pull": 0, "Buy-In": 5000, "Cash-Out": 0}
            self.push_credits = float(data.get("Push", 0))
            self.pull_credits = float(data.get("Pull", 0))
            self.buy_in_credits = float(data.get("Buy-In", 0))
            self.cash_out_credits = float(data.get("Cash-Out", 0))
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON in {filename}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading move from {filename}: {e}")
    
    def __repr__(self):
        return (
            f"Move(date='{self.date}', user='{self.user_name}', project='{self.project}', "
            f"push_credits={self.push_credits}, pull_credits={self.pull_credits}, "
            f"buy_in_credits={self.buy_in_credits}, cash_out_credits={self.cash_out_credits})"
        )

