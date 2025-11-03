# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

Contrived Capital Game is a Python-based economic simulation game that tracks players, plots (business opportunities), moves (player actions), and bank transactions over time. The game processes events chronologically through a timeline system and validates data integrity.

## Common Commands

### Running the Game
```bash
python3 main.py
# Or make it executable and run directly:
./main.py
```

The game automatically:
1. Loads data from directories (Players/, Plots/, Moves/, BankTransactions/)
2. Validates all game data
3. Processes events chronologically
4. Outputs final game state including owed bank transactions

### Python Environment
```bash
# Activate virtual environment (if using venv)
source venv/bin/activate

# Python version: 3.13+ (check with `python3 --version`)
```

## Architecture

### Data Flow
1. **Loading Phase** (`state.py`): Loads JSON files from directories into objects
2. **Validation Phase** (`validation.py`): Validates data integrity and timeline constraints
3. **Timeline Processing** (`timeline.py`): Processes events chronologically using iterator pattern
4. **Output Phase** (`output.py`): Displays final state and calculates owed transactions

### Core Components

#### Game Singleton (`game.py`)
- Central state manager using singleton pattern
- Manages: players (list), plots (10 plots), bank (transactions)
- Setup method initializes game with 10 plots and assigns each player 1 Carry Point per plot

#### Event System (`event.py`)
- Base class for all timeline events (Player, Plot, Move, BankTransaction)
- Events are sortable by date using `get_date_as_datetime()`
- Supports multiple date formats: YYYY-MM-DD and ISO 8601

#### Entity Classes
- **Player** (`player.py`): Has investor_points_in_hand, carry_points_in_hand, credits
- **Plot** (`plot.py`): Business opportunity with cost, conversion_ratio, hurdle_rate, ledger, and solvency_state
- **Move** (`move.py`): Player actions with push_credits, pull_credits, buy_in_credits, cash_out_credits
- **BankTransaction** (`bank_transaction.py`): Real-world USD transactions with cost_usd and revenue_usd

#### Ledger System (`ledger.py`)
- Tracks financial state per Plot
- Maintains: balance, investor_points per player, hurdle, carry_points per player
- Hurdle = total_investor_points × conversion_ratio (credits owed to investors)

#### Timeline Iterator (`timeline.py`)
- `TimelineIterator`: Step-by-step event processing for debugging
- Processes moves: Push (add carry points), Pull (remove carry points), Buy-In (credits → investor points), Cash-Out (credits → coins)
- Tracks cash-out moves for bank transaction matching

### Directory Structure

#### Data Directories (JSON files with .txt extension)
- **Players/**: `LastnameFirstname.txt` format (e.g., `ReardonSean.txt`)
- **Plots/**: `ProductName.txt` format (e.g., `AquaLife.txt`)
- **Moves/**: `YYYY-MM-DD-UserName-ProjectName.txt` format (e.g., `2024-01-20-SeanReardon-Mamani.txt`)
- **BankTransactions/**: `YYYY-MM-DD-AccountId.txt` format (e.g., `2024-01-15-ACC-001.txt`)

#### JSON Schema Examples

**Player JSON** (Players/LastnameFirstname.txt):
```json
{
  "display_name": "First Last",
  "date_joined": "2024-01-20T00:00:00Z",
  "account": "PLAYER-001",
  "email": "user@example.com"
}
```

**Plot JSON** (Plots/ProductName.txt):
```json
{
  "date_started": "2024-02-10T00:00:00Z",
  "account": "ACC-001",
  "product_name": "ProductName",
  "url": "https://drive.google.com/...",
  "description": "Business opportunity description",
  "cost": 85000,
  "conversion_ratio": 4000,
  "hurdle_rate": 0.035
}
```

**Move JSON** (Moves/YYYY-MM-DD-UserName-ProjectName.txt):
```json
{
  "project": "ProductName",
  "Push": 0,
  "Pull": 0,
  "Buy-In": 5000,
  "Cash-Out": 0
}
```

**BankTransaction JSON** (BankTransactions/YYYY-MM-DD-AccountId.txt):
```json
{
  "account": "ACC-001",
  "date": "2024-01-15",
  "Cost": 5000.00,
  "Revenue": 0.00
}
```

### Validation System (`validation.py`)

The validation system performs comprehensive checks:

1. **Data Integrity**: Validates Move references to Players and Plots, checks uniqueness of names/accounts
2. **Timeline Constraints**: Ensures Moves don't occur before Player.date_joined or Plot.date_started
3. **Bank Matching**: Validates bank account strings match Player or Plot accounts

Validation errors halt execution; warnings are displayed but allow continuation.

### Name Matching Convention

- **Filename parsing**: `LastnameFirstname.txt` → internal name `FirstnameLastname` (no space)
- **Move files**: Use FirstnameLastname format for user_name
- **Display**: Use `display_name` field from JSON for user-facing output

## Development Notes

### Testing
No formal test framework is configured. To test changes:
1. Modify data files in respective directories
2. Run `python3 main.py` to see results
3. Check validation output for errors/warnings

### Debugging Timeline
The iterator pattern allows step-by-step debugging:
```python
iterator = timeline.iterator()
while iterator.has_next():
    # Set breakpoint here to inspect state
    event_info = iterator.get_current_event_info()
    iterator.turn()
    iterator = iterator.next()
```

### Adding New Event Types
1. Inherit from `Event` base class
2. Implement `get_date_as_datetime()` if using custom date format
3. Add to Timeline's event list in `create_timeline()`
4. Update Timeline's event processing logic if needed

### Solvency States (Plot)
- **UNDERWATER**: Default state, plot is not yet profitable
- **PAYING_INVESTORS**: Plot covers investor obligations
- **PAYING_PROFIT**: Plot covers investors and generates profit for carry holders

Note: Solvency state transitions are not yet implemented in the current codebase.
