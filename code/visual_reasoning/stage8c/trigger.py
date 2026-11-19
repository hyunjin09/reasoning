"""Causal streaming equivalent of frozen gap4 episode onsets."""
import math

TAU = 0.5478025980771918


class OnlineEpisodes:
    def __init__(self):
        self.last_active = None
        self.position = -1

    def step(self, score):
        self.position += 1
        if not math.isfinite(score):
            self.last_active = None
            return False
        if score <= TAU:
            return False
        onset = self.last_active is None or self.position-self.last_active-1 > 4
        self.last_active = self.position
        return onset
