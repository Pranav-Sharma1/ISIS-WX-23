import numpy as np

from scipy.constants import c, m_p, e


def synchrotron_momentum(emax, time):
  mpeV = m_p * c**2 / e           # Proton mass in eV
  R0 = 26                         # Mean machine radius
  n_dip = 10                      # Number of dipoles
  dip_l = 4.4                     # Dipole length
  
  dip_angle = 2 * np.pi / n_dip   # Dipole bending angle
  rho = dip_l / dip_angle         # Dipole radius of curvature
  omega = 2 * np.pi * 50   
  
  Ek = np.array([70, emax]) * 1e6  # Injection and extraction kinetic energies 
  E = Ek + mpeV                    # Injection and extraction kinetic energies
  p = np.sqrt(E**2 - mpeV**2)      # Injection and extraction momenta

  B = p / c / rho                  # Ideal magnetic field at injection and extraction energies
  
  Bdip = lambda t: (B[1] + B[0] - (B[1] - B[0]) * np.cos(omega * t)) / 2  # Idealised B-field variation with AC
  pdip = lambda t: Bdip(t) * rho * c                                      # Momentum from B-field in MeV
  
  return pdip(time*1E-3)

def synchrotron_kinetic_energy(emax, time, unit = "eV"):
  mpeV = m_p * c**2 / e           # Proton mass in eV    
  # Relativistic Kinetic Energy = Relativistic Energy - mass
  return (
    (np.sqrt(synchrotron_momentum(emax, time) ** 2 + mpeV ** 2) - mpeV) /
    (1E6 if unit.upper() == "MEV" else 1)
  )
