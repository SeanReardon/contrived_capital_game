"""
Validation functions for game data integrity checks.
"""

from typing import List, Set
from collections import Counter
from game import Game
from player import Player
from plot import Plot
from move import Move
from bank import Bank
from bank_transaction import BankTransaction
from timeline import Timeline


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


def validate_game_data(
    game: Game,
    moves: List[Move]
) -> List[str]:
    """
    Perform comprehensive validation of game data.
    
    Checks:
    1. Moves reference valid Players and Plots
    2. Uniqueness of Player names
    3. Uniqueness of Plot product_names
    4. Uniqueness of account strings within Players
    5. Uniqueness of account strings within Plots
    6. Bank account strings match Player or Plot accounts
    
    Args:
        game: Game instance with loaded players, plots, and bank
        moves: List of Move objects
        
    Returns:
        List of warning/error messages (empty if all checks pass)
        
    Raises:
        ValidationError: If critical validation errors are found
    """
    errors = []
    warnings = []
    
    if game.bank is None:
        raise ValidationError("Game.bank must be initialized before validation")
    
    # 1. Check Move references to Players
    player_names = {p.name for p in game.players}
    move_player_errors = []
    for move in moves:
        if move.user_name not in player_names:
            move_player_errors.append(
                f"Move {move.filename} references player '{move.user_name}' "
                f"which does not exist in Players"
            )
    
    if move_player_errors:
        errors.extend(move_player_errors)
    
    # 2. Check Move references to Plots
    plot_names = {p.product_name for p in game.plots if p.product_name}
    move_plot_errors = []
    for move in moves:
        if move.project not in plot_names:
            move_plot_errors.append(
                f"Move {move.filename} references plot '{move.project}' "
                f"which does not exist in Plots"
            )
    
    if move_plot_errors:
        errors.extend(move_plot_errors)
    
    # 3. Check uniqueness of Player names
    player_name_counts = Counter(p.name for p in game.players)
    duplicate_player_names = [name for name, count in player_name_counts.items() if count > 1]
    if duplicate_player_names:
        errors.append(
            f"Duplicate Player names found: {', '.join(duplicate_player_names)}"
        )
    
    # 4. Check uniqueness of Plot product_names
    plot_name_counts = Counter(
        p.product_name for p in game.plots if p.product_name
    )
    duplicate_plot_names = [name for name, count in plot_name_counts.items() if count > 1]
    if duplicate_plot_names:
        errors.append(
            f"Duplicate Plot product_names found: {', '.join(duplicate_plot_names)}"
        )
    
    # 5. Check uniqueness of account strings within Players
    player_accounts = [p.account for p in game.players if p.account]
    player_account_counts = Counter(player_accounts)
    duplicate_player_accounts = [acc for acc, count in player_account_counts.items() if count > 1]
    if duplicate_player_accounts:
        errors.append(
            f"Duplicate account strings in Players: {', '.join(duplicate_player_accounts)}"
        )
    
    # 6. Check uniqueness of account strings within Plots
    plot_accounts = [p.account for p in game.plots if p.account]
    plot_account_counts = Counter(plot_accounts)
    duplicate_plot_accounts = [acc for acc, count in plot_account_counts.items() if count > 1]
    if duplicate_plot_accounts:
        errors.append(
            f"Duplicate account strings in Plots: {', '.join(duplicate_plot_accounts)}"
        )
    
    # 7. Check Bank account strings match Player or Plot accounts
    all_valid_accounts = set(player_accounts + plot_accounts)
    bank_accounts = {t.account for t in game.bank.transactions if t.account}
    
    for bank_account in bank_accounts:
        if bank_account not in all_valid_accounts:
            warnings.append(
                f"Bank transaction references account '{bank_account}' "
                f"which does not exist in any Player or Plot"
            )
    
    # 8. Check that Plots have product_name (required for Move references)
    plots_without_name = [p for p in game.plots if not p.product_name]
    if plots_without_name:
        errors.append(
            f"{len(plots_without_name)} Plot(s) missing product_name "
            f"(required for Move references)"
        )
    
    # 9. Check for invalid dates in Moves
    move_date_errors = []
    for move in moves:
        if move.get_date_as_datetime() is None:
            move_date_errors.append(
                f"Move {move.filename} has invalid date format: '{move.date}' "
                f"(expected YYYY-MM-DD)"
            )
    
    if move_date_errors:
        errors.extend(move_date_errors)
    
    # 10. Check for invalid dates in Bank transactions
    bank_date_errors = []
    for transaction in game.bank.transactions:
        if transaction.get_date_as_datetime() is None:
            bank_date_errors.append(
                f"Bank transaction {transaction.filename} has invalid date format: "
                f"'{transaction.date}' (expected YYYY-MM-DD)"
            )
    
    if bank_date_errors:
        errors.extend(bank_date_errors)
    
    # 11. Check for negative amounts in Moves (warnings, not errors)
    for move in moves:
        if move.push_credits < 0 or move.pull_credits < 0 or \
           move.buy_in_credits < 0 or move.cash_out_credits < 0:
            warnings.append(
                f"Move {move.filename} has negative credit amounts"
            )
    
    # 12. Check for negative amounts in Bank transactions (warnings)
    for transaction in game.bank.transactions:
        if transaction.cost_usd < 0 or transaction.revenue_usd < 0:
            warnings.append(
                f"Bank transaction {transaction.filename} has negative USD amounts"
            )
    
    # Raise ValidationError if there are critical errors
    if errors:
        error_message = "Validation Errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValidationError(error_message)
    
    # Return warnings
    return warnings


def validate_timeline(timeline: Timeline) -> List[str]:
    """
    Validate timeline-based constraints.
    
    Checks:
    1. Moves cannot occur before the player's date_joined
    2. Moves cannot occur before the plot's date_started
    3. Moves should reference plots that exist at that point in time
    
    Args:
        timeline: Timeline instance with all events
        
    Returns:
        List of warning/error messages (empty if all checks pass)
        
    Raises:
        ValidationError: If critical validation errors are found
    """
    errors = []
    warnings = []
    
    # Build a map of when players joined and plots started
    player_join_dates = {}
    plot_start_dates = {}
    
    for event in timeline.events:
        if isinstance(event, Player):
            dt = event.get_date_as_datetime()
            if dt:
                player_join_dates[event.name] = dt
        elif isinstance(event, Plot):
            dt = event.get_date_as_datetime()
            if dt and event.product_name:
                plot_start_dates[event.product_name] = dt
    
    # Check each move against timeline constraints
    for event in timeline.events:
        if isinstance(event, Move):
            move_dt = event.get_date_as_datetime()
            if not move_dt:
                continue
            
            # Check if move is before player joined
            if event.user_name in player_join_dates:
                player_join_dt = player_join_dates[event.user_name]
                if move_dt < player_join_dt:
                    errors.append(
                        f"Move {event.filename} on {event.date} occurs before "
                        f"player '{event.user_name}' joined on {player_join_dt.strftime('%Y-%m-%d')}"
                    )
            
            # Check if move is before plot started
            if event.project in plot_start_dates:
                plot_start_dt = plot_start_dates[event.project]
                if move_dt < plot_start_dt:
                    errors.append(
                        f"Move {event.filename} on {event.date} occurs before "
                        f"plot '{event.project}' started on {plot_start_dt.strftime('%Y-%m-%d')}"
                    )
            
            # Check if plot exists at the time of the move
            # (need to check if plot was started before or on the move date)
            if event.project not in plot_start_dates:
                # Already caught by validate_game_data, but worth noting here too
                pass
            else:
                plot_start_dt = plot_start_dates[event.project]
                if move_dt < plot_start_dt:
                    # Already handled above
                    pass
    
    # Raise ValidationError if there are critical errors
    if errors:
        error_message = "Timeline Validation Errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValidationError(error_message)
    
    return warnings


def print_validation_summary(errors: List[str], warnings: List[str]):
    """
    Print a formatted validation summary.
    
    Args:
        errors: List of error messages
        warnings: List of warning messages
    """
    if errors:
        print("\n" + "="*60)
        print("VALIDATION ERRORS")
        print("="*60)
        for error in errors:
            print(f"  ERROR: {error}")
        print("="*60)
    
    if warnings:
        print("\n" + "="*60)
        print("VALIDATION WARNINGS")
        print("="*60)
        for warning in warnings:
            print(f"  WARNING: {warning}")
        print("="*60)
    
    if not errors and not warnings:
        print("\n✓ All validation checks passed!")

