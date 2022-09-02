class TradeState:
    CREATED = 'created' # Trade created but order not yet placed.
    ACTIVE = 'active' # Order placed and trade is active.
    COMPLETED = 'completed' # Completed when exits due to SL/Target/Squareoff.
    CANCELLED = 'cancelled' # Cancelled/Rejected comes under this state only.
    DISABLED = 'disabled' # disable trade if not triggered within the time limits.