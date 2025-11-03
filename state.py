"""
State loading functions for the game.
"""

import sys
from datetime import datetime
from pathlib import Path
from plot import Plot
from player import Player
from move import Move
from game import Game
from bank import Bank
from validation import validate_game_data, validate_timeline, ValidationError, print_validation_summary
from timeline import create_timeline
from output import calculate_owed_bank_transactions, print_final_state


def load_plots_from_directory(plots_dir: str = None) -> list[Plot]:
    """
    Load plots from JSON files in the plots directory.
    
    Each Plot instance loads itself from its JSON file.
    
    Args:
        plots_dir: Directory containing plot JSON files (defaults to Plot.DATA_DIRECTORY)
        
    Returns:
        List of Plot objects, sorted by date_started
    """
    if plots_dir is None:
        plots_dir = f"./{Plot.DATA_DIRECTORY}"
    plots = []
    plots_path = Path(plots_dir)
    
    if not plots_path.exists():
        raise FileNotFoundError(f"Plots directory not found: {plots_dir}")
    
    # Load all .txt JSON files - Plot class handles loading itself
    for json_file in sorted(plots_path.glob("*.txt")):
        try:
            plot = Plot(filename=str(json_file))
            plots.append(plot)
        except Exception as e:
            print(f"Warning: Failed to load plot from {json_file}: {e}", file=sys.stderr)
    
    # Sort by date_started (ISO 8601 format)
    plots.sort(key=lambda p: p.date_started if p.date_started else "")
    
    # Take first 10 plots
    if len(plots) > 10:
        print(f"Warning: Found {len(plots)} plots, using first 10 by date", file=sys.stderr)
        plots = plots[:10]
    elif len(plots) < 10:
        print(f"Warning: Found only {len(plots)} plots, expected 10", file=sys.stderr)
    
    return plots


def load_players_from_directory(players_dir: str = None) -> list[Player]:
    """
    Load players from JSON files in the Players directory.
    
    Each Player instance loads itself from its JSON file.
    
    Args:
        players_dir: Directory containing player JSON files (defaults to Player.DATA_DIRECTORY)
        
    Returns:
        List of Player objects, sorted by date_joined
    """
    if players_dir is None:
        players_dir = f"./{Player.DATA_DIRECTORY}"
    players = []
    players_path = Path(players_dir)
    
    if not players_path.exists():
        raise FileNotFoundError(f"Players directory not found: {players_dir}")
    
    # Load all .txt JSON files - Player class handles loading itself
    for json_file in sorted(players_path.glob("*.txt")):
        try:
            player = Player(filename=str(json_file))
            players.append(player)
        except Exception as e:
            print(f"Warning: Failed to load player from {json_file}: {e}", file=sys.stderr)
    
    # Sort by date_joined (ISO 8601 format)
    players.sort(key=lambda p: p.date_joined if p.date_joined else "")
    
    return players


def load_state(game: Game, plots_dir: str = None, players_dir: str = None):
    """
    Load the complete game state from JSON files and populate the Game instance.
    
    Loads all plots and players from their respective directories and initializes
    them into the provided Game instance. Performs validation and displays game state.
    Exits the program with error code 1 if any errors occur.
    
    Args:
        game: Game instance to populate with players and plots
        plots_dir: Directory containing plot JSON files (defaults to Plot.DATA_DIRECTORY)
        players_dir: Directory containing player JSON files (defaults to Player.DATA_DIRECTORY)
    """
    try:
        # Load plots
        try:
            plots = load_plots_from_directory(plots_dir)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Cannot load game state: {e}")
        
        if len(plots) == 0:
            raise ValueError("No plots found to load")
        
        # Load players
        try:
            players = load_players_from_directory(players_dir)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Cannot load game state: {e}")
        
        if len(players) == 0:
            raise ValueError("No players found to load")
        
        # Populate the game instance and run setup
        game.setup(players=players, plots=plots)
        
        # Load moves and bank
        moves = load_moves_from_directory()
        game.bank = load_bank()
        
        # Perform validation
        try:
            warnings = validate_game_data(game, moves)
            print_validation_summary([], warnings)
        except ValidationError as e:
            print(f"\n{e}", file=sys.stderr)
            print("\nPlease fix the validation errors before continuing.", file=sys.stderr)
            sys.exit(1)
        
        # Create timeline and validate timeline constraints
        timeline = create_timeline(game, game.players, game.plots, moves, game.bank.transactions)
        try:
            timeline_warnings = validate_timeline(timeline)
            if timeline_warnings:
                print_validation_summary([], timeline_warnings)
        except ValidationError as e:
            print(f"\n{e}", file=sys.stderr)
            print("\nPlease fix the timeline validation errors before continuing.", file=sys.stderr)
            sys.exit(1)
        
        # Return timeline and moves for processing in main
        # The actual event processing will happen in main.py for better debugging
        return timeline, moves
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Make sure the './{Plot.DATA_DIRECTORY}' and './{Player.DATA_DIRECTORY}' directories exist with JSON files.", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def load_moves_from_directory(moves_dir: str = None) -> list[Move]:
    """
    Load moves from JSON files in the moves directory.
    
    Each Move instance loads itself from its JSON file.
    
    Args:
        moves_dir: Directory containing move JSON files (defaults to Move.DATA_DIRECTORY)
        
    Returns:
        List of Move objects, sorted by date
    """
    if moves_dir is None:
        moves_dir = f"./{Move.DATA_DIRECTORY}"
    moves = []
    moves_path = Path(moves_dir)
    
    if not moves_path.exists():
        # Moves directory is optional - if it doesn't exist, return empty list
        return moves
    
    # Load all .txt JSON files - Move class handles loading itself
    for json_file in sorted(moves_path.glob("*.txt")):
        try:
            move = Move(filename=str(json_file))
            moves.append(move)
        except Exception as e:
            print(f"Warning: Failed to load move from {json_file}: {e}", file=sys.stderr)
    
    # Sort by date
    moves.sort(key=lambda m: (m.get_date_as_datetime() or datetime.min))
    
    return moves


def sort_moves_with_balance_priority(moves: list[Move], game: Game) -> list[Move]:
    """
    Sort moves by date, then by player balance (smaller balances first) for same-day moves.
    
    This ensures that players with smaller balances benefit first when multiple moves
    occur on the same day.
    
    Args:
        moves: List of Move objects
        game: Game instance to look up player balances
        
    Returns:
        List of Move objects sorted by date, then by player balance
    """
    # Create a mapping of player names to their total balance
    def get_player_balance(player_name: str) -> float:
        """Get total balance (credits + investor_points value) for a player."""
        # Find player by name (FirstLast format)
        player = None
        for p in game.players:
            if p.name == player_name:
                player = p
                break
        
        if player is None:
            # Player not found, return 0 (unknown players go last)
            return float('inf')
        
        # Calculate total value: credits + investor_points value
        # For investor_points, we need to estimate their value based on plots they're invested in
        # For now, just use credits as the balance indicator
        return player.credits
    
    # Sort by date first, then by player balance (smaller first)
    sorted_moves = sorted(
        moves,
        key=lambda m: (
            m.get_date_as_datetime() or datetime.min,
            get_player_balance(m.user_name)
        )
    )
    
    return sorted_moves


def load_bank(transactions_dir: str = None) -> Bank:
    """
    Load bank transactions and create a Bank instance.
    
    Args:
        transactions_dir: Directory containing bank transaction JSON files
                         (defaults to BankTransaction.DATA_DIRECTORY)
        
    Returns:
        Bank instance with loaded transactions
    """
    return Bank(transactions_dir)

