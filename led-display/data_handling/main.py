from copy import deepcopy

import numpy as np

# from energy_ramp import synchrotron_momentum, synchrotron_kinetic_energy
from .data_filter import DataFilter
from .time_intervals import TimeInterval
from .integrate import integrate_data


def get_data(data, *,
  integrate = True,
  max_energy = 800,
  intervals = None,
):
  ''''''

  out = deepcopy(data)

  # segment
  if intervals != None:
    interval = TimeInterval()
    interval.set_intervals(intervals)
    out = interval.apply(out)[0]
  
  # filter
  get_data.filterer = DataFilter()
  out = get_data.filterer.apply(out)

  # integrate
  if integrate:
    out = integrate_data(out)

  return out
