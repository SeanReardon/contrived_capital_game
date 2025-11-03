# TODO - Contrived Capital Game

## High Priority

### 1. Data Input System
- [ ] **Command-line interface for creating new game data**
  - Support creating new Players via CLI arguments
    - Fields: name, display_name, date_joined, account, email
    - Validate: name uniqueness, date format, etc.
    - Generate JSON file in Players/ directory
  - Support creating new Plots via CLI arguments
    - Fields: story, cost, conversion_ratio, hurdle_rate, date_started, account, product_name, url
    - Validate: product_name uniqueness, date format, etc.
    - Generate JSON file in Plots/ directory
  - Support creating new Moves via CLI arguments
    - Fields: date, user_name, project, push_credits, pull_credits, buy_in_credits, cash_out_credits
    - Validate: user_name exists, project exists, date format, timeline constraints
    - Generate JSON file in Moves/ directory
  - **Validation flow**: After creating data, load full game state and run all validations
    - Must pass game_data validation
    - Must pass timeline validation (for moves)
    - Must not break existing game state
  - **CLI structure**: `python3 main.py create player --name "JohnDoe" --display-name "John Doe" ...`
  - **Bank transactions**: Put aside for now (manual JSON editing)

### 2. Game Mechanics Clarification
- [ ] **Investment Points vs Investor Points**
  - What exactly are "Investment Points"? 
  - Are they the same as "Investor Points" (currently in code)?
  - How do they differ from "Carry Points"?
  - What's the relationship between Investment Points and the conversion_ratio?

- [ ] **Profit Points**
  - What are "Profit Points"?
  - How are they earned/distributed?
  - Relationship to Carry Points and Investor Points?
  - Are they the same as "paid_out_profit_total" in the ledger?

- [ ] **Conversion Ratio**
  - Currently: `conversion_ratio` is Credits/Investor Point
  - When converting credits to investor points via Buy-In, we use: `investor_points = credits / conversion_ratio`
  - Is this correct? Are there other conversions needed?
  - Does conversion_ratio affect anything else?

- [ ] **Hurdle Rate**
  - Currently: `hurdle_rate` is stored as a percentage (e.g., 0.025 for 2.5%)
  - It's stored in Plot, and ledger has a `hurdle` field
  - How is hurdle_rate calculated/used?
  - What does the ledger `hurdle` field represent?
  - When does a plot transition from "Underwater" to "Paying Investors" or "Paying Profit"?

- [ ] **Solvency States**
  - What triggers state transitions?
  - UNDERWATER → PAYING_INVESTORS: When?
  - PAYING_INVESTORS → PAYING_PROFIT: When?
  - What calculations determine these transitions?

- [ ] **Revenue Generation**
  - How does revenue get generated for plots?
  - Is this the "Banker Phase" mentioned in turn_manager.py?
  - How is revenue distributed to investors vs carry holders?
  - How does hurdle_rate affect revenue distribution?

- [ ] **Push/Pull Mechanics**
  - Push: Currently moves carry points from hand to plot
  - Pull: Currently moves carry points from plot back to hand
  - Is `push_credits` actually in credits or carry points?
  - What's the relationship between credits and carry points for Push/Pull?

- [ ] **Buy-In Mechanics**
  - Buy-In converts credits to investor points using conversion_ratio
  - Where do credits come from? (Players start with 0)
  - Do credits come from plot profit distributions?
  - Are credits earned or given?

- [ ] **Cash-Out Mechanics**
  - Cash-Out converts credits to coins (one-way, permanent)
  - What are "coins"? Are they USD?
  - How does cash-out_credits relate to USD deposits?
  - Currently we track cash-out moves and match with bank transactions

## Medium Priority

### 3. Timeline Processing
- [ ] **Event processing order for same-date events**
  - Currently: Events on same date are sorted by object type/order
  - Need: Principle of "benefiting players with smaller balances before larger players"
  - How to determine "balance" for sorting? (total credits? investor points?)
  - Implement balance-based sorting for same-date moves

- [ ] **Player/Plot initialization in timeline**
  - Currently: Player and Plot events are just tracked, not processed
  - Should they have any initialization logic when encountered in timeline?
  - Or are they purely informational for timeline validation?

### 4. Credit Flow
- [ ] **Credit sources**
  - Players start with 0 credits
  - How do players acquire credits?
  - From plot profit distributions?
  - Need to implement revenue distribution logic

- [ ] **Profit Distribution**
  - When/how are plot profits distributed?
  - How are profits split between investor points holders and carry points holders?
  - What role does hurdle_rate play?
  - How do conversion_ratios factor in?

### 5. Bank Transaction Matching
- [ ] **Matching algorithm improvements**
  - Currently: Matches cash-out moves to bank transactions by account, date (±30 days), amount
  - Assumes 1 credit = 1 USD (may need adjustment)
  - Consider: More flexible date windows, amount tolerances, partial matches
  - Handle cases where multiple cash-outs match one transaction or vice versa

- [ ] **Bank transaction validation**
  - Currently: Only validates account strings match players/plots
  - Could add: Date reasonableness checks, amount validations
  - Relationship to moves timeline validation?

## Lower Priority / Future Enhancements

### 6. Code Quality
- [ ] **Type hints**
  - Ensure all functions have complete type hints
  - Add return type hints where missing

- [ ] **Documentation**
  - Add docstrings to all public methods
  - Document game mechanics clearly
  - Create architecture documentation

- [ ] **Testing**
  - Unit tests for each class
  - Integration tests for timeline processing
  - Validation tests

### 7. Data Management
- [ ] **Data editing**
  - Support editing existing JSON files via CLI
  - Validate changes don't break game state
  - Handle re-validation after edits

- [ ] **Data deletion**
  - Support removing players/plots/moves
  - Validate no dangling references
  - Clean up related data if needed

### 8. Output Improvements
- [ ] **Final state reporting**
  - More detailed breakdowns of plot financials
  - Player portfolio summaries
  - Historical transaction summaries
  - Export to CSV/JSON for analysis

- [ ] **Debugging output**
  - Verbose mode showing each event as it's processed
  - State snapshots at key points
  - Timeline visualization

### 9. Game Logic Implementation
- [ ] **Revenue generation**
  - Implement Banker Phase logic
  - Roll dice/flip coin for revenue (from turn_manager.py comments)
  - Calculate and distribute profits

- [ ] **State transitions**
  - Implement solvency state change logic
  - Update plot states based on ledger calculations
  - Track state change history

### 10. Outstanding Questions
- [ ] **Move date priority**
  - For moves on same date, should we also consider:
    - Time of day (if provided)?
    - Order in which they were created?
    - Other factors?

- [ ] **Plot lifecycle**
  - Can plots be removed from the table?
  - Can new plots be added mid-game?
  - What happens to investments in removed plots?

- [ ] **Player lifecycle**
  - Can players leave the game?
  - What happens to their investments?
  - Can new players join mid-game?

- [ ] **Carry Points mechanics**
  - Why does each plot give each player 1 carry point at setup?
  - Do carry points regenerate/refresh?
  - Maximum carry points per player?

- [ ] **Investor Points mechanics**
  - Maximum investor points per plot per player?
  - Can investor points be sold/traded?
  - What happens to investor points when plot is removed?

- [ ] **Currency types**
  - Credits (in-game currency)
  - Coins (one-way conversion from credits, USD?)
  - USD (real-world currency in bank transactions)
  - Relationship and conversion rates between these?

- [ ] **Timeline completeness**
  - Should we validate that all dates make chronological sense?
  - Should we check for gaps in timeline?
  - Should we validate that game state is consistent at each point?

## Notes

- Bank transaction creation is deferred - manual JSON editing for now
- Focus on understanding game mechanics before implementing revenue/profit logic
- Timeline iterator is set up for debugging - can step through events one at a time
- Game instance owns bank object for cleaner architecture

