import numpy as np

from .data_filter import DataFilter
from .time_intervals import TimeInterval


def get_data(data, *,
  max_energy = 800,
  intervals = None,
):
  ''''''

  out = data

  # segment
  if intervals != None:
    interval = TimeInterval()
    interval.set_intervals(intervals)
    out = interval.apply(out)
  
  # filter
  get_data.filterer = DataFilter()

  if data is None:
    return
  
  out = get_data.filterer.apply(out)

  # integrate
  ...

  return out
