"""
BankTransaction class representing a real-world USD transaction.
"""

import json
from typing import Optional
from pathlib import Path
from datetime import datetime
from event import Event


class BankTransaction(Event):
    """
    A BankTransaction represents a real-world USD transaction.
    
    Class Attributes:
        DATA_DIRECTORY: Name of the subdirectory containing bank transaction JSON files
    
    Attributes:
        filename: Original filename of the transaction
        account: Account string identifier
        date: Date of the transaction (YYYY-MM-DD format)
        cost_usd: Amount of money in USD sent (default 0)
        revenue_usd: Amount of money in USD received (default 0)
    """
    
    DATA_DIRECTORY = "BankTransactions"
    
    def __init__(
        self,
        filename: Optional[str] = None,
        account: Optional[str] = None,
        date: Optional[str] = None,
        cost_usd: float = 0.0,
        revenue_usd: float = 0.0
    ):
        """
        Initialize a BankTransaction.
        
        Can be initialized from a JSON file or by providing individual parameters.
        If filename is provided, it loads from that file. Otherwise, uses provided parameters.
        
        Args:
            filename: Path to JSON file to load from (optional)
            account: Account string identifier (required if filename not provided)
            date: Date of the transaction in YYYY-MM-DD format (required if filename not provided)
            cost_usd: Amount of money in USD sent (default 0)
            revenue_usd: Amount of money in USD received (default 0)
        """
        if filename:
            # Load from JSON file
            self._load_from_file(filename)
        else:
            # Initialize from parameters
            if account is None or date is None:
                raise ValueError("Either filename must be provided, or account and date must be provided")
            
            self.filename = f"{date}-{account}.txt"
            self.account = account
            self.date = date
            super().__init__(event_date=date)
            self.cost_usd = cost_usd
            self.revenue_usd = revenue_usd
    
    def _load_from_file(self, filename: str):
        """
        Load bank transaction data from a JSON file.
        
        The filename format is not strictly enforced, but should identify the transaction.
        JSON structure:
        {
            "account": "ACC-001",
            "date": "2024-01-15",
            "Cost": 1000.00,
            "Revenue": 0.00
        }
        
        Args:
            filename: Path to JSON file
        """
        file_path = Path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Bank transaction file not found: {filename}")
        
        self.filename = file_path.name
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract required fields
            self.account = data.get("account", "")
            self.date = data.get("date", "")
            super().__init__(event_date=self.date)
            self.cost_usd = float(data.get("Cost", 0))
            self.revenue_usd = float(data.get("Revenue", 0))
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON in {filename}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading bank transaction from {filename}: {e}")
    
    def net_usd(self) -> float:
        """
        Calculate the net USD amount (revenue - cost).
        
        Returns:
            Net USD amount (positive for net revenue, negative for net cost)
        """
        return self.revenue_usd - self.cost_usd
    
    def __repr__(self):
        return (
            f"BankTransaction(date='{self.date}', account='{self.account}', "
            f"cost_usd={self.cost_usd}, revenue_usd={self.revenue_usd}, "
            f"net={self.net_usd()})"
        )

