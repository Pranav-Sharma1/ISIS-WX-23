'''
LED Display
Main GUI
'''

import sys
import multiprocessing

from copy import deepcopy
from functools import partial

import numpy as np
import paho.mqtt.client as mqtt

from PyQt5 import QtCore as qc
from PyQt5 import QtWidgets as qw


from data_handling.main import get_data
from data_handling.data_filter import DataFilter


### constants
class config:
  count = 39
  
  multiselect = False
  connected = False

  settings = [deepcopy({
    "select": False,
    "shown": True,
    "intervalLower": -0.5,
    "intervalUpper": 10.5,
    "unit": "volts",
    "voltsLower": -0.05229529921101352,
    "voltsUpper": 0.007973001229908228,
    "joulesLower": -8.378630646392451e-21,
    "joulesUpper": 1.2774156273412224e-21,
    "protonsLower": -67432701825.388306,
    "protonsUpper": 27743252085.485558,
    "coulombsLower": -1.0803909923212628e-08,
    "coulombsUpper": 4.444959024253673e-09,
  }) for i in range(count)]

  class data:
    start = -0.5
    stop = 10.5

  class screen:
    x = 1600
    y = 900

  class leds:
    rows = 10
    cols = 4
    size = 50
    space = round(size / 2)

    class style:
      class col:
        idle = "#888"
        norm = "#70c720"
        concern = "#ffc720"
        doom = "#ff0040"
        crash = "#ff0090"

  class buttons:
    x = 100
    y = 40

  class inputs:
    x = 100
    y = 35

  class style:
    font = "Comic Sans MS, Segoe UI"


### main window
class Core(qw.QMainWindow):

  ## setup
  def __init__(self, queue):
    super().__init__()

    ## MQTT
    self.data = []
    self.queue = queue

    def on_connect(client, userdata, flags, rc):
      print("MQTT: CONNECTED!")
      client.subscribe("ac_phys/workxp/live_signals")
      config.connected = True

    def on_message(client, userdata, msg):
      msg_byte = msg.payload
      msg_array = np.frombuffer(msg_byte, dtype = float, count = -1, offset = 0)
      msg_data = np.reshape(msg_array, (40, 2200))

      self.data = get_data(msg_data, intervals = [config.data.start, config.data.stop])
      self.update_all()

      print("\ncycle executed\n")

    def on_disconnect(client, userdata, rc):
      config.connected = False
      if rc != 0:
        print("MQTT: UNEXPECTED DISCONNECT!")
      else:
        print("MQTT: DISCONNECTED!")

    self.client = mqtt.Client()
    self.client.on_connect = on_connect
    self.client.on_message = on_message
    self.client.on_disconnect = on_disconnect


    ## PyQt
    self.setWindowTitle("BLM Monitor")
    self.setMinimumSize(qc.QSize(config.screen.x, config.screen.y))
    self.setStyleSheet(f"*{{font-family:{config.style.font}}}")

    self.root = qw.QWidget()
    self.setCentralWidget(self.root)

    # led grid
    self.ledGridWidget = qw.QWidget(self.root)
    self.ledGridWidget.setGeometry(qc.QRect(50, 50,
      (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space,
      (config.leds.size + config.leds.space) * config.leds.rows + config.leds.space,
    ))
    self.ledGridLayout = qw.QGridLayout(self.ledGridWidget)

    self.create_leds(config.leds.rows, config.leds.cols, skip = [2])

    # row labels
    for i in range(config.leds.rows):
      label = vars(self)[f"row{i+1}"] = qw.QLabel(self.root)
      label.setText(f"R{i}")
      label.setGeometry(qc.QRect(25,
        75 + (config.leds.size + config.leds.space) * i,
      25, 25))

    # col labels
    for i in range(config.leds.cols):
      label = vars(self)[f"col{i+1}"] = qw.QLabel(self.root)
      label.setText(f"BLM{i+1}")
      label.setGeometry(qc.QRect(
        75 + (config.leds.size + config.leds.space) * i,
      25, 50, 25))

    # select button
    self.buttonSelect = qw.QPushButton(self.root)
    self.buttonSelect.setText("Select")
    self.buttonSelect.setGeometry(qc.QRect(
      50 + config.leds.space,
      50 + (config.leds.size + config.leds.space) * config.leds.rows + config.leds.space,
      config.buttons.x,
      config.buttons.y,
    ))
    self.buttonSelect.state = False
    self.buttonSelect.clicked.connect(partial(self.operate, "buttonSelect"))

    # select all button
    self.buttonSelectAll = qw.QPushButton(self.root)
    self.buttonSelectAll.setText("Select All")
    self.buttonSelectAll.setGeometry(qc.QRect(
      50 + config.leds.space * 2 + config.buttons.x,
      50 + (config.leds.size + config.leds.space) * config.leds.rows + config.leds.space,
      config.buttons.x,
      config.buttons.y,
    ))
    self.buttonSelectAll.setEnabled(False)
    self.buttonSelectAll.state = False
    self.buttonSelectAll.clicked.connect(partial(self.operate, "buttonSelectAll"))

    # connect button
    self.buttonConnect = qw.QPushButton(self.root)
    self.buttonConnect.setText("Connect")
    self.buttonConnect.setGeometry(qc.QRect(
      50 + config.leds.space * 3 + config.buttons.x * 2,
      50 + (config.leds.size + config.leds.space) * config.leds.rows + config.leds.space,
      config.buttons.x,
      config.buttons.y,
    ))
    self.buttonConnect.state = False
    self.buttonConnect.clicked.connect(partial(self.operate, "buttonConnect"))

    # selected BLM
    self.selectedLabel = qw.QLabel(self.root)
    self.selectedLabel.setText("-")
    self.selectedLabel.setGeometry(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50,
    50, 500, 75)
    self.selectedLabel.setStyleSheet(f"font-family: {config.style.font}, Segoe UI; font-size: 24pt")

    # shown checkbox
    self.checkboxShown = qw.QCheckBox(self.root)
    self.checkboxShown.setText("Display")
    self.checkboxShown.setGeometry(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50,
    150, 250, 50)
    self.checkboxShown.setEnabled(False)
    self.checkboxShown.setTristate(True)
    self.checkboxShown.stateChanged.connect(partial(self.operate, "checkboxShown"))

    # unit checkboxes
    self.labelUnit = qw.QLabel(self.root)
    self.labelUnit.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50,
    250, 100, 20))
    self.labelUnit.setText("Unit")

    self.radioVolts = qw.QRadioButton(self.root)
    self.radioVolts.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50,
    300, 100, 20))
    self.radioVolts.setText("Volts")
    self.radioVolts.clicked.connect(partial(self.operate, "radioVolts"))
    self.radioJoules = qw.QRadioButton(self.root)
    self.radioJoules.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50,
    350, 100, 20))
    self.radioJoules.setText("Joules")
    self.radioJoules.clicked.connect(partial(self.operate, "radioJoules"))
    self.radioProtons = qw.QRadioButton(self.root)
    self.radioProtons.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50,
    400, 100, 20))
    self.radioProtons.setText("Protons")
    self.radioProtons.clicked.connect(partial(self.operate, "radioProtons"))
    self.radioCoulombs = qw.QRadioButton(self.root)
    self.radioCoulombs.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50,
    450, 100, 20))
    self.radioCoulombs.setText("Coulombs")
    self.radioCoulombs.clicked.connect(partial(self.operate, "radioCoulombs"))

    # threshold input
    self.labelThreshold = qw.QLabel(self.root)
    self.labelThreshold.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 200,
    250, 100, 20))
    self.labelThreshold.setText("Thresholds")

    self.inputVoltsLower = qw.QLineEdit(self.root)
    self.inputVoltsLower.setMaximumSize(qc.QSize(400, 50))
    self.inputVoltsLower.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 200,
    300, config.inputs.x, config.inputs.y))
    self.inputVoltsLower.setText(str(config.settings[0]["voltsLower"]))
    self.inputVoltsLower.textChanged.connect(partial(self.operate, "inputVoltsLower", "volts", "lower"))
    self.inputJoulesLower = qw.QLineEdit(self.root)
    self.inputJoulesLower.setMaximumSize(qc.QSize(400, 50))
    self.inputJoulesLower.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 200,
    350, config.inputs.x, config.inputs.y))
    self.inputJoulesLower.setText(str(config.settings[0]["joulesLower"]))
    self.inputJoulesLower.textChanged.connect(partial(self.operate, "inputJoulesLower", "joules", "lower"))
    self.inputProtonsLower = qw.QLineEdit(self.root)
    self.inputProtonsLower.setMaximumSize(qc.QSize(400, 50))
    self.inputProtonsLower.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 200,
    400, config.inputs.x, config.inputs.y))
    self.inputProtonsLower.setText(str(config.settings[0]["protonsLower"]))
    self.inputProtonsLower.textChanged.connect(partial(self.operate, "inputProtonsLower", "protons", "lower"))
    self.inputCoulombsLower = qw.QLineEdit(self.root)
    self.inputCoulombsLower.setMaximumSize(qc.QSize(400, 50))
    self.inputCoulombsLower.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 200,
    450, config.inputs.x, config.inputs.y))
    self.inputCoulombsLower.setText(str(config.settings[0]["coulombsLower"]))
    self.inputCoulombsLower.textChanged.connect(partial(self.operate, "inputCoulombsLower", "coulombs", "lower"))

    self.inputVoltsUpper = qw.QLineEdit(self.root)
    self.inputVoltsUpper.setMaximumSize(qc.QSize(400, 50))
    self.inputVoltsUpper.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 200 + config.inputs.x + 50,
    300, config.inputs.x, config.inputs.y))
    self.inputVoltsUpper.setText(str(config.settings[0]["voltsUpper"]))
    self.inputVoltsUpper.textChanged.connect(partial(self.operate, "inputVoltsUpper", "volts", "upper"))
    self.inputJoulesUpper = qw.QLineEdit(self.root)
    self.inputJoulesUpper.setMaximumSize(qc.QSize(400, 50))
    self.inputJoulesUpper.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 200 + config.inputs.x + 50,
    350, config.inputs.x, config.inputs.y))
    self.inputJoulesUpper.setText(str(config.settings[0]["joulesUpper"]))
    self.inputJoulesUpper.textChanged.connect(partial(self.operate, "inputJoulesUpper", "joules", "upper"))
    self.inputProtonsUpper = qw.QLineEdit(self.root)
    self.inputProtonsUpper.setMaximumSize(qc.QSize(400, 50))
    self.inputProtonsUpper.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 200 + config.inputs.x + 50,
    400, config.inputs.x, config.inputs.y))
    self.inputProtonsUpper.setText(str(config.settings[0]["protonsUpper"]))
    self.inputProtonsUpper.textChanged.connect(partial(self.operate, "inputProtonsUpper", "protons", "upper"))
    self.inputCoulombsUpper = qw.QLineEdit(self.root)
    self.inputCoulombsUpper.setMaximumSize(qc.QSize(400, 50))
    self.inputCoulombsUpper.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 200 + config.inputs.x + 50,
    450, config.inputs.x, config.inputs.y))
    self.inputCoulombsUpper.setText(str(config.settings[0]["coulombsUpper"]))
    self.inputCoulombsUpper.textChanged.connect(partial(self.operate, "inputCoulombsUpper", "coulombs", "upper"))

    # intervals input
    self.labelIntervals = qw.QLabel(self.root)
    self.labelIntervals.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50,
    550, 100, 20))
    self.labelIntervals.setText("Intervals")

    self.inputIntervalLower = qw.QLineEdit(self.root)
    self.inputIntervalLower.setMaximumSize(qc.QSize(400, 50))
    self.inputIntervalLower.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50,
    600, config.inputs.x, config.inputs.y))
    self.inputIntervalLower.setText(str(config.data.start))
    self.inputIntervalLower.textChanged.connect(partial(self.operate, "inputIntervalLower"))
    self.inputIntervalUpper = qw.QLineEdit(self.root)
    self.inputIntervalUpper.setMaximumSize(qc.QSize(400, 50))
    self.inputIntervalUpper.setGeometry(qc.QRect(
      50 + (config.leds.size + config.leds.space) * config.leds.cols + config.leds.space + 50 + config.inputs.x + 50,
    600, config.inputs.x, config.inputs.y))
    self.inputIntervalUpper.setText(str(config.data.stop))
    self.inputIntervalUpper.textChanged.connect(partial(self.operate, "inputIntervalUpper"))

    self.update_all()

  
  ## utility
  def create_leds(self,
    rows: int,
    cols: int,
    *,
    size: tuple[int, int] = (config.leds.size,) * 2,
    skip = [],
  ):
    '''Automates creation of LED button elements.'''

    offset = 0
    for i in range(rows):
      for k in range(cols):
        idx = i * cols + k + 1
        if idx in skip:
          offset += 1
          continue
        idx -= offset

        label = f"led{idx}"
        led = vars(self)[label] = qw.QPushButton(self.ledGridWidget)
        led.label = f"led{idx}"
        led.setMaximumSize(qc.QSize(*size))
        led.setObjectName(led.label)
        led.setText(f"{idx}")
        led.styleDict = {
          "color": "rgb(255, 255, 255)",
          "background-color": config.leds.style.col.idle,
          "border": "transparent",
          "border-color": "rgb(0, 0, 0)",
          "border-width": "3px",
        }
        led.clicked.connect(partial(self.select, idx - 1))

        self.ledGridLayout.addWidget(led, i, k, 1, 1)

  def update_style(self, component):
    '''Updates stylesheet of `component` based on its `styleDict`.'''

    component.setStyleSheet("; ".join(f"{key}:{value}" for key, value in component.styleDict.items()))

  def update_all(self):
    '''Update appearances of LEDs and the current selection information.'''

    # update leds
    for i, each in enumerate(config.settings):
      led = vars(self)[f"led{i+1}"]

      if self.data:
        try:
          led.styleDict["background-color"] = (
            config.leds.style.col.idle if not config.connected else
            config.leds.style.col.doom if sum(self.data[i]) > each[f"{each['unit']}Upper"] else
            config.leds.style.col.concern if sum(self.data[i]) > each[f"{each['unit']}Lower"] else
            config.leds.style.col.norm
          )
        except:
          led.styleDict["background-color"] = config.leds.style.crash

      if each["select"]:
        led.styleDict["border-style"] = "solid"
        led.styleDict["border-color"] = "#000"
      else:
        led.styleDict["border-style"] = "transparent"
        
      if each["shown"]:
        led.styleDict["opacity"] = 1
      else:
        led.styleDict["opacity"] = 0.5

      self.update_style(led)

    # update menu
    selection = [i for i, each in enumerate(config.settings) if each["select"]]
    selected = len(selection)
    self.selectedLabel.setText(
      "Multiple Selected" if selected > 1 else
      DataFilter.labels[selection[0]].upper() if selected == 1
      else "-"
    )

    self.checkboxShown.setEnabled(selected)
    self.checkboxShown.setCheckState(all(each["shown"] for each in config.settings) * 2 or 1)

    # update unit
    unit = set(each["unit"] for each in config.settings if each["select"])
    if len(unit) == 1:
      unit = unit.pop()
      vars(self)[f"radio{unit.capitalize()}"].setChecked(True)
    else:
      self.radioVolts.setChecked(False)
      self.radioJoules.setChecked(False)
      self.radioProtons.setChecked(False)
      self.radioCoulombs.setChecked(False)

    search = lambda query: set(each[query] for each in config.settings if each["select"])

    lower = search("voltsLower")
    self.inputVoltsLower.setText("" if len(lower) != 1 else str(lower.pop()))
    lower = search("joulesLower")
    self.inputJoulesLower.setText("" if len(lower) != 1 else str(lower.pop()))
    lower = search("protonsLower")
    self.inputProtonsLower.setText("" if len(lower) != 1 else str(lower.pop()))
    lower = search("coulombsLower")
    self.inputCoulombsLower.setText("" if len(lower) != 1 else str(lower.pop()))
    
    upper = search("voltsUpper")
    self.inputVoltsUpper.setText("" if len(upper) != 1 else str(upper.pop()))
    upper = search("joulesUpper")
    self.inputJoulesUpper.setText("" if len(upper) != 1 else str(upper.pop()))
    upper = search("protonsUpper")
    self.inputProtonsUpper.setText("" if len(upper) != 1 else str(upper.pop()))
    upper = search("coulombsUpper")
    self.inputCoulombsUpper.setText("" if len(upper) != 1 else str(upper.pop()))

    # update intervals
    lower = search("intervalLower")
    self.inputIntervalLower.setText("" if len(lower) != 1 else str(lower.pop()))
    upper = search("intervalUpper")
    self.inputIntervalUpper.setText("" if len(upper) != 1 else str(upper.pop()))

  
  ## event handlers
  def select(self, label):
    '''Handle response to an LED button being clicked.'''

    selected = config.settings[label]["select"]
    if not config.multiselect and not selected:
      for each in config.settings:
        each["select"] = False
    config.settings[label]["select"] = not selected
    
    self.update_all()

  def operate(self, label, *args):
    '''Handle response to a button with `label` being clicked.'''

    button = vars(self)[label]

    match label:
      case "buttonSelect":
        button.state = not button.state
        config.multiselect = button.state
        button.setText("Cancel" if button.state else "Select")

        if not button.state:
          for each in config.settings:
            each["select"] = False
        
        self.buttonSelectAll.setEnabled(button.state)
        self.buttonSelectAll.setText("Select All")

      case "buttonSelectAll":
        button.state = not button.state
        for each in config.settings:
          each["select"] = button.state
        button.setText("Deselect All" if button.state else "Select All")

      case "buttonConnect":
        if button.state:
          try:
            self.client.loop_stop()
            self.client.disconnect()
          except:
            raise
          else:
            button.state = False
            button.setText("Connect")
        
        else:
          try:
            self.client.connect("130.246.57.45", 8883, 60)
            self.client.loop_start()
          except:
            raise
          else:
            button.state = True
            button.setText("Disconnect")

      case "checkboxShown":        
        for each in config.settings:
          if each["select"]:
            each["shown"] = self.checkboxShown.checkState()

      case "radioVolts" | "radioJoules" | "radioProtons" | "radioCoulombs":
        for each in config.settings:
          if each["select"]:
            each["unit"] = label[5:].lower()

      case "inputIntervalLower":
        for each in config.settings:
          if each["select"]:
            each["intervalLower"] = self.inputIntervalLower.text()

      case "inputIntervalUpper":
        for each in config.settings:
          if each["select"]:
            each["intervalUpper"] = self.inputIntervalUpper.text()

      case _:
        # thresholds
        if label.startswith("input"):
          for each in config.settings:
            if each["select"]:
              setting = f"{args[0]}{args[1].capitalize()}"
              each[setting] = vars(self)[f"input{setting[0].upper() + setting[1:]}"].text()

    self.update_all()


### execution
if __name__ == "__main__":  
  queue = multiprocessing.Queue()

  root = qw.QApplication(sys.argv)

  core = Core(queue)
  core.show()

  sys.exit(root.exec())
