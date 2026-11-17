"""
classify.py — why did each visit happen?  **You design this one.**

Every visit gets one of the five reasons in settings.REASONS:

    on the way to work   stopped on the trip from home to work
    during work          a break from work, near work
    on the way home      stopped on the trip from work to home
    near home            near where they live (weekends, mornings off, evenings)
    other                none of these: an event, shopping, visiting a friend

Nobody told us the reasons. You decide which features matter and where the
cut-offs go, then check your rules against the survey with the scorer
(`python code/check_score.py`). Look at your results on the charts, too: if
"on the way to work" visits show up at 2 p.m., your rules are off.

You start from a baseline that works: it uses only the clock. Run check_score.py
on it first. It agrees with the survey on about 76% of visits, and never says
"other" (0%). To pass you need 85% overall and 60% for every reason. Look at
what it gets wrong (most_confused_with), ask what would tell those visits apart
— usually a place, not a time: d_home, d_work, detour, has_work — change one
thing, and score again.

Keep your cut-offs in named constants at the top of this file, like these, so
they are easy to find and change.
"""

import numpy as np
import pandas as pd

from .settings import (
    DURING_WORK,
    NEAR_HOME,
    ON_THE_WAY_HOME,
    ON_THE_WAY_TO_WORK,
    OTHER,
)

WORK_STARTS_BY = 9.5      # hour: weekday visits before this are the commute in
WORK_ENDS_BY = 15.5       # hour: weekday visits before this are during work
EVENING_ENDS_BY = 19.5    # hour: weekday visits before this are the commute home

NEAR_HOME_KM = 2.5        # distance in km to shop for "near home"
NEAR_WORK_KM = 2.5        # distance in km from work to shop for "during work"
MAX_DETOUR_KM = 2.0       # maximum detour in km for commute


def classify_visits(visits: pd.DataFrame) -> pd.DataFrame:
    """`visits` (from add_features) with a new `reason` column: one of the five
    reasons in settings.REASONS for every row.

    A new DataFrame, same rows in the same order; `visits` is not changed.

    The baseline: `np.select` checks the conditions in order and gives each row
    the reason of the first one that is true, or the default. Improve it.
    """
    result = visits.copy()
    weekday = result["weekday"]
    hour = result["hour"]
    has_work = result["has_work"]
    d_home = result["d_home"]
    d_work = result["d_work"]
    detour = result["detour"]

    is_commute_in = (
        weekday
        & has_work
        & (hour < WORK_STARTS_BY)
        & (detour <= MAX_DETOUR_KM)
    )
    is_during_work = (
        weekday
        & has_work
        & (hour >= WORK_STARTS_BY)
        & (hour < WORK_ENDS_BY)
        & (d_work <= NEAR_WORK_KM)
    )
    is_commute_home = (
        weekday
        & has_work
        & (hour >= WORK_ENDS_BY)
        & (hour < EVENING_ENDS_BY)
        & (detour <= MAX_DETOUR_KM)
    )
    is_near_home = d_home <= NEAR_HOME_KM

    result["reason"] = np.select(
        [
            is_commute_in,
            is_during_work,
            is_commute_home,
            is_near_home,
        ],
        [
            ON_THE_WAY_TO_WORK,
            DURING_WORK,
            ON_THE_WAY_HOME,
            NEAR_HOME,
        ],
        default=OTHER,
    )
    return result
