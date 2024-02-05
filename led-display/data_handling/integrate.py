import numpy as np
import scipy as sp


def integrate_data(data):
  # TODO: implement support for time intervals
  
  out = []

  for each in data:
    integral = sp.integrate.cumulative_trapezoid(each, x = np.linspace(-0.5, 10.5, 2200))
    integral = np.diff(integral)
    out.append(integral)

  return out
