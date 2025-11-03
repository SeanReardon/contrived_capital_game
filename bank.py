"""
Bank class representing bank transactions tied to the game.
"""

from typing import Optional, List
from pathlib import Path
from datetime import datetime
from bank_transaction import BankTransaction


class Bank:
    """
    A Bank manages real-world USD transactions tied to the game.
    
    Attributes:
        transactions: List of BankTransaction objects, sorted by date
    """
    
    def __init__(self, transactions_dir: Optional[str] = None):
        """
        Initialize a Bank and load transactions.
        
        Args:
            transactions_dir: Directory containing bank transaction JSON files
                            (defaults to BankTransaction.DATA_DIRECTORY)
        """
        if transactions_dir is None:
            transactions_dir = f"./{BankTransaction.DATA_DIRECTORY}"
        
        self.transactions: List[BankTransaction] = []
        self._load_transactions(transactions_dir)
    
    def _load_transactions(self, transactions_dir: str):
        """
        Load bank transactions from JSON files in the directory.
        
        Args:
            transactions_dir: Directory containing bank transaction JSON files
        """
        transactions_path = Path(transactions_dir)
        
        if not transactions_path.exists():
            # Transactions directory is optional - if it doesn't exist, just return
            return
        
        # Load all .txt JSON files
        for json_file in sorted(transactions_path.glob("*.txt")):
            try:
                transaction = BankTransaction(filename=str(json_file))
                self.transactions.append(transaction)
            except Exception as e:
                print(f"Warning: Failed to load bank transaction from {json_file}: {e}")
        
        # Sort by date
        self.transactions.sort(key=lambda t: (t.get_date_as_datetime() or datetime.min))
    
    def get_account_balance(self, account: str) -> float:
        """
        Calculate the total balance for a given account.
        
        Args:
            account: Account string identifier
            
        Returns:
            Total net USD balance (revenue - cost) for the account
        """
        balance = 0.0
        for transaction in self.transactions:
            if transaction.account == account:
                balance += transaction.net_usd()
        return balance
    
    def get_transactions_by_account(self, account: str) -> List[BankTransaction]:
        """
        Get all transactions for a given account.
        
        Args:
            account: Account string identifier
            
        Returns:
            List of BankTransaction objects for the account, sorted by date
        """
        return [t for t in self.transactions if t.account == account]
    
    def __repr__(self):
        return (
            f"Bank(transactions={len(self.transactions)}, "
            f"unique_accounts={len(set(t.account for t in self.transactions))})"
        )

