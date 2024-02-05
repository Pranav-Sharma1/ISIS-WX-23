import numpy as np


class TimeInterval:
  def __init__(self, *, start = -0.5, end = 10.5, points = 2200):
    self.start = start
    self.end = end
    self.points = points

  def set_intervals(self, intervals):
    self.intervals = [
      round((each - self.start) / (self.end - self.start)) * self.points
      for each in intervals
    ]
    self.intervals = list(zip(self.intervals, self.intervals[1:]))
  
  def apply(self, data: np.array) -> list[np.array]:
    return [data[start:end] for start, end in self.intervals]
  
  def sum_times(self, data, signal, pairs):
    return [sum(data[signal][start:end]) for start, end in pairs]
