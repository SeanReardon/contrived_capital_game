"""
Turn Manager module for handling turn-based game logic.
"""

from typing import Dict, Any
from game import Game
from plot import Plot


def execute_turn(game: Game) -> Dict[str, Any]:
    """
    Execute a single turn of the game, managing all three phases.
    
    Phases:
    1. New Plot Phase: Add a new plot to the table, give each player a Carry Point
    2. Player Action Phase: Each player takes their actions in turn (placeholder)
    3. Banker Phase: Resolve revenue for all plots (placeholder)
    
    Args:
        game: The Game instance containing players and plots
        
    Returns:
        Dictionary containing information about what happened during the turn
        
    Note:
        This is a simplified implementation. Phase 2 and 3 are placeholders for future work.
    """
    turn_info = {
        "phase_1": {},
        "phase_2": {},
        "phase_3": {}
    }
    
    # Phase 1: New Plot Phase
    # For now, we start with 10 plots already on the table from setup
    # In a full implementation, this would add a new plot and give each player a Carry Point
    turn_info["phase_1"]["message"] = "All plots are already on the table from initial setup"
    turn_info["phase_1"]["total_plots"] = len(game.plots)
    
    # Phase 2: Player Action Phase
    # Placeholder for player actions
    # In a full implementation, each player would:
    # - Place Carry Points on plots
    # - Spend Credits on Investor Points
    # - Take Credits from the game (convert to Coins)
    turn_info["phase_2"]["message"] = "Player actions not yet implemented"
    turn_info["phase_2"]["players"] = [p.name for p in game.players]
    
    # Phase 3: Banker Phase
    # Placeholder for revenue resolution
    # In a full implementation, the banker would:
    # - Roll 2d6 and flip a coin for each plot to generate revenue
    # - Apply revenue to each plot's ledger
    # - Distribute payments to investors and carry holders
    # - Update solvency states
    turn_info["phase_3"]["message"] = "Banker resolution not yet implemented"
    turn_info["phase_3"]["plots_resolved"] = 0
    
    return turn_info


def print_turn_summary(turn_info: Dict[str, Any]):
    """
    Print a formatted summary of the turn execution.
    
    Args:
        turn_info: The dictionary returned by execute_turn()
    """
    print("\n" + "="*60)
    print("TURN SUMMARY")
    print("="*60)
    
    print(f"\nPhase 1 - New Plot: {turn_info['phase_1']['message']}")
    if "total_plots" in turn_info["phase_1"]:
        print(f"  Total plots on table: {turn_info['phase_1']['total_plots']}")
    
    print(f"\nPhase 2 - Player Actions: {turn_info['phase_2']['message']}")
    if "players" in turn_info["phase_2"]:
        print(f"  Players: {', '.join(turn_info['phase_2']['players'])}")
    
    print(f"\nPhase 3 - Banker Resolution: {turn_info['phase_3']['message']}")
    if "plots_resolved" in turn_info["phase_3"]:
        print(f"  Plots resolved: {turn_info['phase_3']['plots_resolved']}")
    
    print("="*60)

