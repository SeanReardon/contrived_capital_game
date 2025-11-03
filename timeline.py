"""
Timeline system for processing game events chronologically.
"""

from typing import List
from datetime import datetime
from game import Game
from player import Player
from plot import Plot
from move import Move
from bank_transaction import BankTransaction
from event import Event


class Timeline:
    """
    A Timeline manages all game events and processes them chronologically.
    
    Attributes:
        events: List of all events (Player, Plot, Move, BankTransaction) sorted by date
        game: Game instance being processed
    """
    
    def __init__(self, game: Game, players: List[Player], plots: List[Plot], 
                 moves: List[Move], bank_transactions: List[BankTransaction]):
        """
        Initialize a Timeline with all game events.
        
        Args:
            game: Game instance
            players: List of Player objects
            plots: List of Plot objects
            moves: List of Move objects
            bank_transactions: List of BankTransaction objects
        """
        self.game = game
        self.events: List[Event] = []
        self.cash_out_moves: List[Move] = []
        
        # Add all events to the timeline
        self.events.extend(players)
        self.events.extend(plots)
        self.events.extend(moves)
        self.events.extend(bank_transactions)
        
        # Sort by date (oldest first)
        self.events.sort()
    
    def get_current_date(self) -> datetime:
        """
        Get the current date (most recent event date).
        
        Returns:
            Current datetime, or datetime.min if no events
        """
        if not self.events:
            return datetime.min
        
        current_date = None
        for event in reversed(self.events):
            dt = event.get_date_as_datetime()
            if dt:
                current_date = dt
                break
        
        return current_date if current_date else datetime.min
    
    def iterator(self):
        """
        Create an iterator for stepping through events one at a time.
        
        Returns:
            TimelineIterator instance
        """
        return TimelineIterator(self)
    
    def step_through_events(self):
        """
        Process all events in chronological order (legacy method for compatibility).
        
        Returns:
            List of cash-out moves for bank transaction matching
        """
        iterator = self.iterator()
        while iterator.has_next():
            iterator.turn()
        
        return self.cash_out_moves
    
    def _process_move(self, move: Move):
        """
        Process a Move event.
        
        Handles:
        - Push: Add Carry Points to a Plot
        - Pull: Remove Carry Points from a Plot
        - Buy-In: Convert Credits to Investor Points on a Plot
        - Cash-Out: Convert Credits to Coins (tracked for bank transaction matching)
        
        Args:
            move: Move to process
        """
        # Find the player
        player = None
        for p in self.game.players:
            if p.name == move.user_name:
                player = p
                break
        
        if not player:
            # Should have been caught by validation, but skip if missing
            return
        
        # Find the plot
        plot = None
        for p in self.game.plots:
            if p.product_name == move.project:
                plot = p
                break
        
        if not plot:
            # Should have been caught by validation, but skip if missing
            return
        
        # Process Push (place Carry Points from hand onto Plot)
        if move.push_credits > 0:
            # Push moves carry points from player's hand to the plot
            # The amount is in credits, but represents carry points
            # For now, assuming 1 credit worth = 1 carry point
            # (Note: push_credits may actually represent the value, but we're moving carry points)
            carry_points_to_add = int(move.push_credits)
            available = min(carry_points_to_add, player.carry_points_in_hand)
            if available > 0:
                plot.ledger.add_carry_points(player.name, available)
                player.carry_points_in_hand -= available
        
        # Process Pull (remove Carry Points from Plot back to hand)
        if move.pull_credits > 0:
            # Pull moves carry points from plot back to player's hand
            carry_points_to_remove = int(move.pull_credits)
            current_on_plot = plot.ledger.carry_points.get(player.name, 0)
            available = min(carry_points_to_remove, current_on_plot)
            if available > 0:
                plot.ledger.add_carry_points(player.name, -available)
                player.carry_points_in_hand += available
        
        # Process Buy-In (convert Credits to Investor Points)
        if move.buy_in_credits > 0:
            # Convert credits to investor points using plot's conversion ratio
            investor_points = int(move.buy_in_credits / plot.conversion_ratio)
            if investor_points > 0:
                plot.ledger.add_investor_points(player.name, investor_points, plot.conversion_ratio)
                # Deduct credits from player
                player.credits = max(0, player.credits - move.buy_in_credits)
                # Deduct investor points from player's hand
                player.investor_points_in_hand = max(0, player.investor_points_in_hand - investor_points)
        
        # Process Cash-Out (convert Credits to Coins - one-way, permanent)
        if move.cash_out_credits > 0:
            # Track this for bank transaction matching
            self.cash_out_moves.append(move)
            # Deduct credits from player (one-way conversion to coins)
            player.credits = max(0, player.credits - move.cash_out_credits)


def create_timeline(game: Game, players: List[Player], plots: List[Plot],
                   moves: List[Move], bank_transactions: List[BankTransaction]) -> Timeline:
    """
    Create a Timeline with all game events.
    
    Args:
        game: Game instance
        players: List of Player objects
        plots: List of Plot objects
        moves: List of Move objects
        bank_transactions: List of BankTransaction objects
        
    Returns:
        Timeline instance with sorted events
    """
    return Timeline(game, players, plots, moves, bank_transactions)


class TimelineIterator:
    """
    Iterator for stepping through timeline events one at a time.
    
    Allows for step-by-step debugging by processing events individually.
    """
    
    def __init__(self, timeline: Timeline):
        """
        Initialize the iterator.
        
        Args:
            timeline: Timeline instance to iterate over
        """
        self.timeline = timeline
        self.current_index = 0
        self.cash_out_moves = []
    
    def has_next(self) -> bool:
        """
        Check if there are more events to process.
        
        Returns:
            True if there are more events, False otherwise
        """
        # Skip events without valid dates
        while self.current_index < len(self.timeline.events):
            event = self.timeline.events[self.current_index]
            if event.get_date_as_datetime():
                return True
            self.current_index += 1
        return False
    
    def get_current_event(self) -> Event:
        """
        Get the current event without processing it.
        
        Returns:
            Current Event object
        """
        if self.current_index >= len(self.timeline.events):
            raise IndexError("No more events")
        return self.timeline.events[self.current_index]
    
    def turn(self):
        """
        Process the current event (does not advance).
        
        This processes the current event but does not move the iterator forward.
        Call next() to advance to the next event.
        """
        if not self.has_next():
            return
        
        event = self.timeline.events[self.current_index]
        dt = event.get_date_as_datetime()
        
        if dt:
            if isinstance(event, Move):
                self.timeline._process_move(event)
                # Track cash-out moves (also tracked in timeline, but keep local copy)
                if event.cash_out_credits > 0:
                    self.cash_out_moves.append(event)
                    self.timeline.cash_out_moves.append(event)
            # Player and Plot events are just tracked (they're already in game state)
            # BankTransaction events are just tracked
    
    def next(self):
        """
        Advance to the next event and return this iterator.
        
        This allows for chaining: iterator = iterator.next()
        
        Returns:
            self (for method chaining)
        """
        self.current_index += 1
        return self
    
    def get_progress(self) -> tuple[int, int]:
        """
        Get current iteration progress.
        
        Returns:
            Tuple of (current_index, total_events)
        """
        return (self.current_index, len(self.timeline.events))
    
    def get_current_event_info(self) -> dict:
        """
        Get information about the current event for debugging.
        
        Returns:
            Dictionary with event information
        """
        if not self.has_next():
            return {"status": "no_more_events"}
        
        event = self.timeline.events[self.current_index]
        dt = event.get_date_as_datetime()
        
        return {
            "index": self.current_index,
            "total": len(self.timeline.events),
            "event_type": type(event).__name__,
            "date": event.event_date,
            "datetime": dt.strftime("%Y-%m-%d") if dt else None,
            "event": event
        }

