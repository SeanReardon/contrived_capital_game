#!/usr/bin/env python3
"""
Main program for the Contrived Capital Game.

Loads game data, validates it, processes all events chronologically,
and prints the final state including owed bank transactions.
"""

import sys
from game import Game
from state import load_state
from output import calculate_owed_bank_transactions, print_final_state


def main():
    """
    Main entry point.
    
    Loads game state, validates it, processes the timeline step-by-step,
    and prints final state.
    """
    # Create the game instance
    game = Game()
    
    # Load game state and get timeline for processing
    timeline, moves = load_state(game)
    
    # Process events step-by-step using iterator
    print("\nProcessing timeline events...")
    iterator = timeline.iterator()
    
    while iterator.has_next():
        # Process current event
        # You can inspect the current event with: iterator.get_current_event_info()
        iterator.turn()
        
        # Advance to next event
        # You can set breakpoints here to inspect state after processing each event
        # Useful for debugging: check game.players, game.plots, game.bank, etc.
        iterator = iterator.next()
    
    # Get cash-out moves from the iterator
    cash_out_moves = iterator.cash_out_moves
    
    # Calculate owed bank transactions
    owed_transactions = calculate_owed_bank_transactions(cash_out_moves, game.bank, game.players)
    
    # Print final state
    print_final_state(game, owed_transactions)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

