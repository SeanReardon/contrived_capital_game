"""
Output functions for displaying final game state.
"""

from typing import List, Dict
from datetime import datetime
from game import Game
from player import Player
from plot import Plot
from move import Move
from bank_transaction import BankTransaction
from bank import Bank


def calculate_owed_bank_transactions(
    cash_out_moves: List[Move],
    bank: Bank,
    players: List[Player]
) -> List[Dict]:
    """
    Calculate bank transactions that are owed (cash-out moves without corresponding bank transactions).
    
    Args:
        cash_out_moves: List of cash-out moves
        bank: Bank instance with existing transactions
        players: List of players to match accounts
        
    Returns:
        List of dictionaries with owed transaction details:
        {
            'player_name': str,
            'player_account': str,
            'date': str,
            'amount_usd': float,
            'move': Move object
        }
    """
    owed_transactions = []
    
    # Create a mapping of player name to account
    player_account_map = {p.name: p.account for p in players if p.account}
    
    # Track which cash-outs have been matched to bank transactions
    matched_moves = set()
    
    # For each cash-out move, check if there's a matching bank transaction
    for move in cash_out_moves:
        if move.cash_out_credits <= 0:
            continue
        
        player_account = player_account_map.get(move.user_name)
        if not player_account:
            continue
        
        # Check if there's a bank transaction for this account matching the amount
        # We'll match on account and approximate date/amount
        move_dt = move.get_date_as_datetime()
        if not move_dt:
            continue
        
        # Look for matching bank transaction
        # Match criteria: same account, revenue within reasonable time window (e.g., 30 days)
        matched = False
        for transaction in bank.transactions:
            if transaction.account == player_account:
                trans_dt = transaction.get_date_as_datetime()
                if trans_dt:
                    # Check if transaction is within 30 days of move date
                    days_diff = abs((move_dt - trans_dt).days)
                    if days_diff <= 30:
                        # Check if revenue matches cash-out amount (within small tolerance)
                        # For now, we'll assume credits = USD 1:1 (this may need adjustment)
                        if abs(transaction.revenue_usd - move.cash_out_credits) < 0.01:
                            matched = True
                            matched_moves.add(move)
                            break
        
        # If not matched, it's an owed transaction
        if not matched:
            owed_transactions.append({
                'player_name': move.user_name,
                'player_account': player_account,
                'date': move.date,
                'amount_usd': move.cash_out_credits,
                'move': move
            })
    
    return owed_transactions


def print_final_state(game: Game, owed_transactions: List[Dict]):
    """
    Print the final state of players, plots, and owed bank transactions.
    
    Args:
        game: Game instance with final state
        owed_transactions: List of owed bank transaction dictionaries
    """
    print("\n" + "="*80)
    print("FINAL GAME STATE")
    print("="*80)
    
    # Print Players
    print("\n" + "-"*80)
    print("PLAYERS")
    print("-"*80)
    for player in sorted(game.players, key=lambda p: p.display_name):
        print(f"\n{player.display_name} ({player.name}):")
        print(f"  Investor Points in hand: {player.investor_points_in_hand}")
        print(f"  Carry Points in hand: {player.carry_points_in_hand}")
        print(f"  Credits: {player.credits:,.0f}")
        if player.account:
            print(f"  Account: {player.account}")
        if player.email:
            print(f"  Email: {player.email}")
    
    # Print Plots
    print("\n" + "-"*80)
    print("PLOTS")
    print("-"*80)
    for plot in sorted(game.plots, key=lambda p: p.product_name or ""):
        print(f"\n{plot.product_name or 'Unknown'} ({plot.date_started or 'No date'}):")
        print(f"  Story: {plot.story[:100]}...")
        print(f"  Cost: {plot.cost:,} Credits")
        print(f"  Conversion Ratio: {plot.conversion_ratio:,} Credits/Investor Point")
        print(f"  Hurdle Rate: {plot.hurdle_rate:.1%}")
        print(f"  Solvency State: {plot.solvency_state.value}")
        print(f"  Ledger Balance: {plot.ledger.balance:,} Credits")
        print(f"  Ledger Hurdle: {plot.ledger.hurdle:,} Credits")
        print(f"  Total Investor Points: {plot.ledger.get_total_investor_points()}")
        print(f"  Total Carry Points: {plot.ledger.get_total_carry_points()}")
        print(f"  Paid Out Profit Total: {plot.ledger.paid_out_profit_total:,} Credits")
        if plot.account:
            print(f"  Account: {plot.account}")
        
        # Show investor points breakdown
        if plot.ledger.investor_points:
            print(f"  Investor Points by Player:")
            for player_name, points in sorted(plot.ledger.investor_points.items()):
                if points > 0:
                    print(f"    {player_name}: {points}")
        
        # Show carry points breakdown
        if plot.ledger.carry_points:
            print(f"  Carry Points by Player:")
            for player_name, points in sorted(plot.ledger.carry_points.items()):
                if points > 0:
                    print(f"    {player_name}: {points}")
    
    # Print Owed Bank Transactions
    print("\n" + "-"*80)
    print("OWED BANK TRANSACTIONS")
    print("-"*80)
    if not owed_transactions:
        print("\nNo owed bank transactions.")
    else:
        print(f"\nFound {len(owed_transactions)} owed bank transaction(s):\n")
        for trans in owed_transactions:
            print(f"  Player: {trans['player_name']}")
            print(f"  Account: {trans['player_account']}")
            print(f"  Date: {trans['date']}")
            print(f"  Amount: ${trans['amount_usd']:,.2f} USD")
            print(f"  Move File: {trans['move'].filename}")
            print()
    
    print("="*80)

