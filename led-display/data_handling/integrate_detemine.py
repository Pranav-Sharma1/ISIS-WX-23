import paho.mqtt.client as mqtt
import numpy as np
import threading
import time
import glob
import pandas as pd
import scipy
import matplotlib.pyplot as plt
from scipy import integrate
from scipy.constants import c, m_p, e
from scipy.optimize import minimize

def dataframe(path):
    """Fetch and convert raw data into a numpy array."""
    files = glob.glob(path)
    selected_file = files[0]
    global x_data
    x_data = np.linspace(-0.5, 10.5, 2200)
    input_data = pd.read_csv(selected_file)
    data = input_data.drop(columns=input_data.columns[0]).to_numpy()

    return data


def find_diff_between_adj(array):
    diff_integral = np.diff(array)
    diff_integral = np.insert(diff_integral,0,array[0])
    
    return diff_integral

def get_integral_updated(x, array):
    in_array = get_integral(x, array)
    
    out_array = []
    for i in range(1, len(in_array)):
        out_array.append((in_array[i]-in_array[i-1]))
    
    return np.insert(out_array,0,in_array[0])


def get_integral(x, value):
    integral = scipy.integrate.cumulative_trapezoid(value, x=x)
    
    return integral


def synchrotron_momentum(max_E, time):
    """Calculate synchrotron momentum."""
    mpeV = m_p * c**2 / e
    R0 = 26
    n_dip = 10
    dip_l = 4.4

    dip_angle = 2 * np.pi / n_dip
    rho = dip_l / dip_angle
    omega = 2 * np.pi * 50

    Ek = np.array([70, max_E]) * 1e6
    E = Ek + mpeV
    p = np.sqrt(E**2 - mpeV**2)

    B = p / c / rho

    Bdip = lambda t: (B[1] + B[0] - (B[1] - B[0]) * np.cos(omega * t)) / 2
    pdip = lambda t: Bdip(t) * rho * c

    return pdip(time*1E-3)


def synchrotron_kinetic_energy(max_E, time):
    """Convert time to energy."""
    mpeV = m_p * c**2 / e
    return (np.sqrt(synchrotron_momentum(max_E, time)**2 + mpeV**2) - mpeV) / 1E6


def divided_diff(x, y):
    '''
    function to calculate the divided
    differences table
    '''
    n = len(y)
    coef = np.zeros([n, n])
    # the first column is y
    coef[:,0] = y
    
    for j in range(1,n):
        for i in range(n-j):
            coef[i][j] = \
           (coef[i+1][j-1] - coef[i][j-1]) / (x[i+j]-x[i])
            
    return coef

def newton_poly(coef, x_d, x):
    '''
    evaluate the newton polynomial 
    at x
    '''
    n = len(x_d) - 1 
    p = coef[n]
    for k in range(1,n+1):
        p = coef[n-k] + (x -x_d[n-k])*p
    return p

def get_calibration_curve(data_points):
    
    BLM_Cal_x_time = np.array([0., 3., 5., 7., 9.])
    # mVs/proton
    # BLM_Cal_y = np.array([2.22E-16, 2.59E-16, 4.31E-15, 1.60E-14, 3.50E-14])
    # vS/proton
    BLM_Cal_y = np.array([2.22E-16, 2.59E-16, 4.31E-15, 1.60E-14, 3.50E-14])
    
    a_s = divided_diff(BLM_Cal_x_time, BLM_Cal_y)[0, :]
    time_array = np.linspace(0., 10., data_points)
    
    # Original 1F method
    return newton_poly(a_s, BLM_Cal_x_time, time_array)   
    

def calibration_curve_beta(t_min=-0.5, t_max=10.5, data_points=2200, max_E=800):
    
    BLM_Cal_x_time = np.array([0., 3., 5., 7., 9.])
    # mVs/proton
    # BLM_Cal_y = np.array([2.22E-16, 2.59E-16, 4.31E-15, 1.60E-14, 3.50E-14])
    # vS/proton
    BLM_Cal_y = np.array([2.22E-16, 2.59E-16, 4.31E-15, 1.60E-14, 3.50E-14])
    
    
    time_array = np.linspace(t_min, t_max, data_points)
    
    # Default if in storage ring mode (fixed 70 MeV)
    if max_E == 70: return np.ones(len(time_array))*BLM_Cal_y[0]
    
    # calculate data points to pass to calibration curve (only returns between 0 - 10 ms)
    t_range = t_max - t_min
    # t_excess = t_range - 10.
    t_scale = data_points / t_range # points per millisecond
    #print(t_scale)
    cal_data_points = int(t_scale * 10)    
    pre_data_points = int(t_scale * -t_min)
    post_data_points = int(t_scale * (t_max-10))
    
    assert( (cal_data_points + pre_data_points + post_data_points) == data_points)
    
    a_s = divided_diff(BLM_Cal_x_time, BLM_Cal_y)[0, :]
    
    # Original 1F method
    calibration_curve = get_calibration_curve(cal_data_points) # newton_poly(a_s, BLM_Cal_x_time, time_array)
        
    # Conditional: if time before first calibration data point, fix value
    if np.any(time_array < BLM_Cal_x_time[0]): 
        #calibration_curve[np.where(time_array < 0)] = BLM_Cal_y[0]
        calibration_curve = np.concatenate([np.ones(pre_data_points)*BLM_Cal_y[0], calibration_curve])
    
    # Find Maximum - dependent on energy
    cal_max = 4.63E-14 # default to interpolated 800 MeV value

    # Conditional: if time before first calibration data point, fix value
    if np.any(time_array > 10.): 
        #calibration_curve[np.where(time_array < 0)] = BLM_Cal_y[0]
        calibration_curve = np.concatenate([calibration_curve, np.ones(post_data_points)*cal_max ])
    
    # Conditional: between first two points use linear interpolation
    
    #calibration_curve[np.where(time_array < 0)] = BLM_Cal_y[0]
        
        
    return calibration_curve

def div_coef(y, coef):
    """Divide n*m BLM integration array by coefficient array."""
    result = []
    for row in y:
        stor = np.divide(row, coef)
        result.append(stor)
    return result

def get_integral_updated(x, array):
    in_array = get_integral(x, array)
    out_array = []
    for i in range(1, len(in_array)):
        out_array.append((in_array[i]-in_array[i-1]))
    
    return np.insert(out_array,0,in_array[0])


def get_integral(x, value):
    integral = scipy.integrate.cumulative_trapezoid(value, x=x)
    
    return integral

def integrate_data(data):
  integration = []

# Iterating each row of 'b' and append it to 'a'
  for i in range(data.shape[0]):
    row_integral = get_integral_updated(np.linspace(-1.5, 10.5, 2200), data[i, :])
    integration.append(row_integral)
    integration = np.array(integration)
  return integration



class VoltProcessor:
    def __init__(self, data, t1=0, t2=0, coef=None):
        self.data = data
        self.t1 = t1
        self.t2 = t2
        self.coef = coef
        self.judgement = []
        self.integration_by_row = []
        self.integration = None

    def integrate_data(self):
        self.integration = []

# Iterating each row of 'b' and append it to 'a'
        for i in range(self.data.shape[0]):
            row_integral = get_integral_updated(np.linspace(-1.5, 10.5, 2200), self.data[i, :])
            self.integration.append(row_integral)
        self.integration = np.array(self.integration)

    def integrate_by_row(self):
        for row in self.integration:
            self.integration_by_row.append(np.sum(row))
        

    def judge(self):
        for i in self.integration_by_row:
            if self.t1 > i:
                self.judgement.append('good')
            elif self.t1 < i < self.t2:
                self.judgement.append('moderate')
            else:
                self.judgement.append('bad')

    def judging(self):
        self.integrate_data()
        self.integrate_by_row()
        self.judge()
        return self.judgement
    
    def integrate_by_unit(self):
        self.integrate_data()
        return self.integration
    
    def intg_list_row(self):
        self.integrate_data()
        self.integrate_by_row()
        return self.integration_by_row


class ProtonProcessor(VoltProcessor):
    def integrate_data(self):
        self.integration = []

# Iterating each row of 'b' and append it to 'a'
        for i in range(self.data.shape[0]):
            row_integral = get_integral_updated(np.linspace(-1.5, 10.5, 2200), self.data[i, :])
            self.integration.append(row_integral)
        self.integration = div_coef(self.integration, self.coef) 
        self.integration = np.array(self.integration) * 1e-3
        


class ColoumbProcessor(VoltProcessor):
    def integrate_data(self):
        self.integration = []
        for i in range(self.data.shape[0]):
            row_integral = get_integral_updated(np.linspace(-1.5, 10.5, 2200), self.data[i, :])
            self.integration.append(row_integral)
        self.integration = div_coef(self.integration, self.coef)
        self.integration = np.array(self.integration) * 1e-3
        self.integration *= e




class JouleProcessor(VoltProcessor):
    def integrate_data(self):
        self.integration = []
        for i in range(self.data.shape[0]):
            row_integral = get_integral_updated(np.linspace(-1.5, 10.5, 2200), self.data[i, :])
            self.integration.append(row_integral)
        self.integration = np.array(self.integration) 
        self.integration *= e

coef = calibration_curve_beta(t_min=-0.5, t_max=10.5, data_points=2200)[:-1]

def lv5judge(data, t1, t2, thtype):
    if thtype == 'volt':
        processor = VoltProcessor(data, t1, t2)
        
    elif thtype == 'proton':
        processor = ProtonProcessor(data, t1, t2, coef)
    elif thtype == 'coloumbs':
        processor = ColoumbProcessor(data, t1, t2, coef)
    elif thtype == 'joules':
        processor = JouleProcessor(data, t1, t2)
    led_result_array = processor.process()
    return led_result_array

def lv5judge(data, t1, t2, thtype):
    if thtype == 'volt' or thtype == 'v':
        processor = VoltProcessor(data, t1, t2)
        
    elif thtype == 'proton' or thtype == 'p':
        processor = ProtonProcessor(data, t1, t2, coef)
    elif thtype == 'coloumbs' or thtype == 'c':
        processor = ColoumbProcessor(data, t1, t2, coef)
    elif thtype == 'joules' or thtype == 'j':
        processor = JouleProcessor(data, t1, t2)
    led_result_array = processor.judging()
    return led_result_array

def live_int(data, thtype): 
    if thtype == 'volt' or thtype == 'v':
        processor = VoltProcessor(data = data, coef = coef)
    elif thtype == 'proton' or thtype == 'p':
        processor = ProtonProcessor(data = data, coef = coef)
    elif thtype == 'coloumbs' or thtype == 'c':
        processor = ColoumbProcessor(data = data, coef = coef)
    elif thtype == 'joules' or thtype == 'J':
        processor = JouleProcessor(data = data, coef = coef)
    int_value = processor.integrate_by_unit() 
    return int_value 

def live_int_row(data, thtype): 
    if thtype == 'volt' or thtype == 'v':
        processor = VoltProcessor(data = data, coef = coef)
    elif thtype == 'proton' or thtype == 'p':
        processor = ProtonProcessor(data = data, coef = coef)
    elif thtype == 'coloumbs' or thtype == 'c':
        processor = ColoumbProcessor(data = data, coef = coef)
    elif thtype == 'joules' or thtype == 'J':
        processor = JouleProcessor(data = data, coef = coef)
    int_value = processor.intg_list_row()
    return int_value
