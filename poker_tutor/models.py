"""Public API declarations used by FastAPI validation and native OpenAPI."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


Card = Annotated[str, Field(pattern=r"^[2-9TJQKA][cdhs]$")]
ID = Annotated[str, Field(pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", json_schema_extra={"format": "uuid"})]
Action = Literal["check", "bet", "fold"]
Street = Literal["flop", "turn", "river"]
Category = Literal["high_card", "pair", "two_pair", "three_of_a_kind", "straight", "flush",
                   "full_house", "four_of_a_kind", "straight_flush", "royal_flush"]
Amount = Annotated[float, Field(ge=0, le=4_000_000_000, allow_inf_nan=False)]
Change = Annotated[float, Field(ge=-4_000_000_000, le=4_000_000_000, allow_inf_nan=False)]
Probability = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Stacks = Annotated[list[Amount], Field(min_length=4, max_length=4)]
Changes = Annotated[list[Change], Field(min_length=4, max_length=4)]
Board = Annotated[list[Card], Field(min_length=3, max_length=5)]
HoleCards = Annotated[list[Card], Field(min_length=2, max_length=2)]
PrivateCards = Annotated[list[HoleCards], Field(min_length=4, max_length=4)]
Winners = Annotated[list[Annotated[int, Field(ge=0, le=3)]], Field(min_length=1, max_length=4)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyRequest(Model):
    pass


class ActionRequest(Model):
    action: Action
    street: Street


class ContinueRequest(Model):
    street: Street


class APIErrorResponse(Model):
    code: Literal["invalid_request", "validation_error", "unsupported_media_type", "session_not_found",
                  "hand_not_found", "active_session_exists", "active_hand_exists", "session_ended",
                  "session_active", "hand_not_active", "stale_street", "invalid_stage",
                  "replay_step_out_of_range", "insufficient_chips", "simulation_unavailable",
                  "creation_request_replayed"]
    message: str = Field(min_length=1, max_length=1000)
    details: list[dict] | None = None


class GameRules(Model):
    player_count: Literal[4]
    starting_stack: int = Field(ge=1, le=1_000_000_000)
    opening_contribution: int = Field(ge=1, le=1_000_000_000)
    bet_amount: Literal[10]
    opponent_policy: Literal["check_or_call"]
    analysis_policy: Literal["check_down"]


class HandCounts(Model):
    completed: int = Field(ge=0)
    folded: int = Field(ge=0)
    abandoned: int = Field(ge=0)


class GradeCounts(Model):
    good: int = Field(ge=0)
    bad: int = Field(ge=0)
    reasonable: int = Field(ge=0)


class SessionStatistics(Model):
    hands: HandCounts
    decisions: GradeCounts
    net_chips: Change


class SessionResponse(Model):
    id: ID
    status: Literal["active", "ended"]
    created_at: Annotated[str, Field(json_schema_extra={"format": "date-time"})]
    rules: GameRules
    hand_ids: list[ID]
    active_hand_id: ID | None
    statistics: SessionStatistics


class OpponentRange(Model):
    player_index: int = Field(ge=1, le=3)
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=1000)
    hands: list[Annotated[str, Field(pattern=r"^[2-9TJQKA]{2}[so]?$" )]] = Field(min_length=1, max_length=169)


class OutcomeProbabilities(Model):
    outright_win: Probability
    two_way_tie: Probability
    three_way_tie: Probability
    four_way_tie: Probability
    loss: Probability


class WinProbability(Model):
    percent: Annotated[float, Field(ge=0, le=100)]
    confidence_interval_percent: list[Annotated[float, Field(ge=0, le=100)]] = Field(min_length=2, max_length=2)
    confidence_level: Annotated[float, Field(ge=.95, le=.95)]
    display: str = Field(min_length=1, max_length=32)


class ActionEVs(Model):
    check: Change
    bet: Change | None
    fold: Annotated[float, Field(ge=0, le=0)]


class FeedbackResponse(Model):
    action: Action
    street: Street
    decision_board: Board
    pot_before_action: int = Field(ge=1, le=4_000_000_000)
    stacks_before_action: Stacks
    available_actions: list[Action] = Field(min_length=2, max_length=3)
    bet_amount: Literal[10]
    analysis_policy: Literal["check_down"]
    opponent_policy: Literal["check_or_call"]
    simulation_method: Literal["monte_carlo", "exact"]
    sample_count: Literal[0, 10000]
    confidence_level: Annotated[float, Field(ge=.95, le=.95)]
    outcome_probabilities: OutcomeProbabilities
    outright_win_probability: WinProbability
    equity: Probability
    margin_of_error: Probability
    equity_confidence_interval: list[Probability] = Field(min_length=2, max_length=2)
    required_equity: Annotated[float, Field(ge=.25, le=.25)]
    action_evs: ActionEVs
    incremental_bet_ev: Change | None
    recommendation: Literal["check", "bet", "either"]
    acceptable_actions: list[Action] = Field(min_length=1, max_length=3)
    is_correct: bool
    grade: Literal["good", "bad", "reasonable"]
    made_hand: Category
    explanation: list[Annotated[str, Field(min_length=1, max_length=2000)]] = Field(min_length=1, max_length=10)


class ShowdownResponse(Model):
    kind: Literal["actual"]
    private_cards: PrivateCards
    winners: Winners
    winning_hand: Category
    payouts: Stacks
    chip_changes: Changes
    user_chip_change: Change
    pot_awarded: int = Field(ge=1, le=4_000_000_000)


class FoldReviewResponse(Model):
    kind: Literal["hypothetical"]
    private_cards: PrivateCards
    winners: Winners
    winning_hand: Category
    hypothetical_payouts: Stacks
    actual_winners: list[Annotated[int, Field(ge=1, le=3)]] = Field(min_length=1, max_length=3)
    actual_payouts: Stacks
    actual_chip_changes: Changes
    pot_awarded: int = Field(ge=1, le=4_000_000_000)
    user_chip_change: Change
    user_payout: Literal[0]
    explanation: str = Field(min_length=1, max_length=2000)


class HandResponse(Model):
    id: ID
    session_id: ID
    created_at: Annotated[str, Field(json_schema_extra={"format": "date-time"})]
    status: Literal["active", "completed", "folded", "abandoned"]
    street: Street
    stage: Literal["awaiting_action", "awaiting_continuation", "showdown", "fold_review", "abandoned"]
    user_cards: HoleCards
    community_cards: Board
    pot: int = Field(ge=0, le=4_000_000_000)
    stacks: Stacks
    available_actions: list[Action] = Field(max_length=3)
    bet_amount: Literal[10]
    opponent_policy: Literal["check_or_call"]
    opponent_ranges: list[OpponentRange] = Field(min_length=3, max_length=3)
    feedback: FeedbackResponse | None
    showdown: ShowdownResponse | None
    review: FoldReviewResponse | None


class ReplayResponse(Model):
    read_only: Literal[True]
    hand_status: Literal["active", "completed", "folded", "abandoned"]
    step: int = Field(ge=0)
    total_steps: int = Field(ge=1)
    event: Literal["deal", "action", "continue", "abandon"]
    state: HandResponse
