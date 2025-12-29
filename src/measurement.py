"""Measurement Policy: MMM vs MTA decision tree."""

from enum import Enum
from typing import Literal
from dataclasses import dataclass


class MeasurementApproach(str, Enum):
    """Measurement approach."""
    MTA = "mta"
    MMM = "mmm"
    HYBRID = "hybrid"
    RCT_BASED = "rct_based"


@dataclass
class MTAPolicy:
    """Multi-Touch Attribution configuration."""
    optimization_frequency: str  # "daily", "weekly"
    channels: list  # ["facebook", "google", "tiktok"]
    attribution_model: str  # "last_click", "first_click", "linear", "time_decay"
    lookback_window_days: int


@dataclass
class MMMPolicy:
    """Marketing Mix Modeling configuration."""
    optimization_frequency: str  # "quarterly", "monthly"
    channels: list  # ["tv", "digital", "influencer"]
    data_source: str  # "aggregated_historical"
    modeling_horizon_days: int


@dataclass
class IncrementalityTestPolicy:
    """Incrementality testing configuration."""
    enabled: bool
    holdout_size_percent: int  # 10
    duration_days: int  # 14
    measure: str  # "true_causal_lift"


@dataclass
class MeasurementPolicy:
    """Complete measurement policy."""
    approach: MeasurementApproach
    short_cycle: MTAPolicy = None
    long_cycle: MMMPolicy = None
    incrementality_tests: IncrementalityTestPolicy = None

    @classmethod
    def from_data_constraints(
        cls,
        has_user_tracking: bool,
        has_historical_aggregate: bool,
        timeline: Literal["short_term", "long_term"] = "hybrid"
    ) -> "MeasurementPolicy":
        """
        Select measurement approach based on data availability.
        """
        if timeline == "short_term":
            if has_user_tracking:
                approach = MeasurementApproach.MTA
            else:
                approach = MeasurementApproach.HYBRID
        elif timeline == "long_term":
            if has_historical_aggregate:
                approach = MeasurementApproach.MMM
            else:
                approach = MeasurementApproach.RCT_BASED
        else:
            approach = MeasurementApproach.HYBRID

        return cls(
            approach=approach,
            short_cycle=MTAPolicy(
                optimization_frequency="daily",
                channels=["facebook", "google"],
                attribution_model="last_click",
                lookback_window_days=7
            ),
            long_cycle=MMMPolicy(
                optimization_frequency="quarterly",
                channels=["all"],
                data_source="aggregated_historical",
                modeling_horizon_days=90
            ),
            incrementality_tests=IncrementalityTestPolicy(
                enabled=True,
                holdout_size_percent=10,
                duration_days=14,
                measure="true_causal_lift"
            )
        )
