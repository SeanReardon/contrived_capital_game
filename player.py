"""
Player class representing a player in the game.
"""

import json
from typing import Optional
from pathlib import Path
from event import Event


class Player(Event):
    """
    A Player in the game.
    
    Class Attributes:
        DATA_DIRECTORY: Name of the subdirectory containing player JSON files
    
    Attributes:
        name: Player's name in FirstLast format (no space) - used for matching/comparison
        display_name: Player's display name (e.g., "First Last") - used for display
        investor_points_in_hand: Investor Points currently held by the player (starts at 10)
        carry_points_in_hand: Carry Points currently held by the player (starts at 10)
        credits: Credits owned by the player (starts at 0)
    """
    
    DATA_DIRECTORY = "Players"
    
    def __init__(
        self,
        filename: Optional[str] = None,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        date_joined: Optional[str] = None,
        account: Optional[str] = None,
        email: Optional[str] = None
    ):
        """
        Initialize a Player.
        
        Can be initialized from a JSON file or by providing individual parameters.
        If filename is provided, it loads from that file. Otherwise, uses provided parameters.
        
        Args:
            filename: Path to JSON file to load from (optional)
            name: Player's name in FirstLast format (required if filename not provided)
            display_name: Player's display name (optional, defaults to name if not provided)
            date_joined: Date joined in ISO 8601 format (optional)
            account: Account string identifier (optional)
            email: Email address (optional)
        """
        if filename:
            # Load from JSON file
            self._load_from_file(filename)
        else:
            # Initialize from parameters
            if name is None:
                raise ValueError("Either filename must be provided, or name must be provided")
            
            self.name = name  # FirstLast format
            self.display_name = display_name if display_name is not None else name
            super().__init__(event_date=date_joined)
            self.investor_points_in_hand = 10
            self.carry_points_in_hand = 10
            self.credits = 0
            
            # Metadata from JSON
            self.date_joined = date_joined
            self.account = account
            self.email = email
    
    def _load_from_file(self, filename: str):
        """
        Load player data from a JSON file.
        
        The filename should be in the format LastnameFirstname.txt
        (e.g., ReardonSean.txt -> name="SeanReardon", display_name from JSON or "Sean Reardon")
        
        Args:
            filename: Path to JSON file
        """
        file_path = Path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Player file not found: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract player name from filename (LastnameFirstname.txt -> "FirstnameLastname")
            filename_stem = file_path.stem  # Remove .txt extension
            # Try to split into Lastname and Firstname
            # This is a simple heuristic - may need adjustment for edge cases
            first_last_name = filename_stem  # Default to full filename
            # Try to find where the capital letter starts (assuming LastnameFirstname format)
            for i in range(1, len(filename_stem)):
                if filename_stem[i].isupper():
                    lastname = filename_stem[:i]
                    firstname = filename_stem[i:]
                    # name is FirstLast (no space) for matching
                    first_last_name = f"{firstname}{lastname}"
                    break
            
            # Extract required fields
            self.name = first_last_name  # FirstLast format for matching
            # display_name from JSON, or generate from filename
            if "display_name" in data:
                self.display_name = data["display_name"]
            else:
                # Generate display_name from filename if not in JSON
                # LastnameFirstname -> "Firstname Lastname"
                filename_stem = file_path.stem
                for i in range(1, len(filename_stem)):
                    if filename_stem[i].isupper():
                        lastname = filename_stem[:i]
                        firstname = filename_stem[i:]
                        self.display_name = f"{firstname} {lastname}"
                        break
                else:
                    self.display_name = filename_stem
            
            self.date_joined = data.get("date_joined", None)
            super().__init__(event_date=self.date_joined)
            self.account = data.get("account", None)
            self.email = data.get("email", None)
            
            # Initialize game values
            self.investor_points_in_hand = 10
            self.carry_points_in_hand = 10
            self.credits = 0
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON in {filename}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading player from {filename}: {e}")
    
    def __repr__(self):
        return (
            f"Player(name='{self.name}', display_name='{self.display_name}', "
            f"investor_points={self.investor_points_in_hand}, "
            f"carry_points={self.carry_points_in_hand}, "
            f"credits={self.credits})"
        )

