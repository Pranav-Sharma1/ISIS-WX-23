import numpy as np


class TimeInterval:
  def __init__(self, *, start = -0.5, end = 10.5, points = 2200):
    self.start = start
    self.end = end
    self.points = points

  def set_intervals(self, timeIntervals):
    self.timeIntervals = [
      round((each - self.start) / (self.end - self.start) * self.points)
      for each in timeIntervals
    ]
    self.timeIntervals = list(zip(self.timeIntervals, self.timeIntervals[1:]))
    return self.timeIntervals
  
  def setIntervals(self, decimalIntervals):
    self.decimalIntervals = [
      round(each * self.points) for each in decimalIntervals
    ]
    self.decimalIntervals = list(zip(self.decimalIntervals, self.decimalIntervals[1:]))
    return self.decimalIntervals
  
  def apply(self, data: np.array) -> list[np.array]:
    return [data[start:end] for start, end in self.timeIntervals]
  
  def sum_times(self, data, signal, pairs):
    return [sum(data[signal][start:end]) for start, end in pairs]
  
  def proportionOfData(self, dataIntervals: np.array):
    return (dataIntervals[-1][-1] - dataIntervals[0][0])/self.points
