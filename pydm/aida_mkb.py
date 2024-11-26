# generic multiknob controller
import os
import sys
from functools import partial
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QFrame, QGridLayout, QPushButton, QLineEdit, QSlider, QLabel
from epics import get_pv

SELF_PATH = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(*os.path.split(SELF_PATH)[:-1])
sys.path.append(REPO_ROOT)
from slc_mkb import set_mkb

STYLE_BRD_GREEN = """
QFrame{
background-color: rgb(230,230,230);
border-color: rgb(80,255,120);
border-width: 2px;
border-style: solid;
}
"""

STYLE_BRD_RED = """
QFrame{
background-color: rgb(230,230,230);
border-color: rgb(220,0,0);
border-width: 2px;
border-style: solid;
}
"""

STYLE_BRD_BLK = """
QFrame{
background-color: rgb(230,230,230);
border-color: rgb(120,120,120);
border-width: 2px;
border-style: solid;
}
"""

KNOB_LOW = -100
KNOB_HIGH = 100

# default increment in degS
DEFAULT_STEP_SIZE = 1.0

REFRESH_MS = 200

class AIDAMKBController(QFrame):
    """ L2 phase knob, can click to increment/decrement or type deltas """

    def __init__(self, mkname, lim_lo=KNOB_LOW, lim_hi=KNOB_HIGH, parent=None, args=None):
        QFrame.__init__(self, parent=parent)
        self.init_ui()
        self.displacement = 0.0
        self.mkname = mkname
        self.update_readbacks()

    def init_ui(self):
        """ initialize pyqt UI elements, layout etc """
        self.ctl_incr = QPushButton('+')
        self.ctl_decr = QPushButton('-')
        self.ctl_manual = QLineEdit('0.0')
        self.set_mkname = QLineEdit('')
        self.set_step = QLineEdit(f'{DEFAULT_STEP_SIZE:.2f}')
        self.set_lim_lo = QLineEdit(f'{KNOB_LOW:.2f}')
        self.set_lim_hi = QLineEdit(f'{KNOB_HIGH:.2f}')
        self.indicator = QSlider(Qt.Horizontal)

        lbl_name = QLabel("MKB name:")
        lbl_step = QLabel("step:")
        lbl_lims = QLabel("limits (hi/low):")
        self.lbl_low = QLabel(str(KNOB_LOW))
        self.lbl_high = QLabel(str(KNOB_HIGH))

        # enforces numeric input
        self.ctl_manual.setValidator(QDoubleValidator(-1e10, 1e10, 6))
        self.set_step.setValidator(QDoubleValidator(0.0, 1e10, 6))
        self.set_lim_lo.setValidator(QDoubleValidator(-1e10, 1e10, 6))
        self.set_lim_hi.setValidator(QDoubleValidator(-1e10, 1e10, 6))

        self.ctl_decr.setMaximumWidth(40)
        self.ctl_incr.setMaximumWidth(40)
        self.set_step.setMaximumWidth(80)
        lbl_step.setMaximumWidth(80)
        self.lbl_low.setMaximumWidth(50)
        self.lbl_high.setMaximumWidth(50)
        self.lbl_low.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.lbl_high.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

        self.indicator.setEnabled(False) # slider is not interactive
        self.indicator.setMaximum(KNOB_HIGH)
        self.indicator.setMinimum(KNOB_LOW)
        self.indicator.setTickInterval(5)
        self.indicator.setTickPosition(QSlider.TicksBelow)
        self.indicator.setInvertedAppearance(True)

        self.ctl_incr.clicked.connect(self.incr)
        self.ctl_decr.clicked.connect(self.decr)
        self.ctl_manual.returnPressed.connect(self.update_manual)
        self.set_mkname.returnPressed.connect(self.reinit)
        self.set_lim_lo.returnPressed.connect(self.update_limits)
        self.set_lim_hi.returnPressed.connect(self.update_limits)

        L = QGridLayout()

        # row 1: slider readback
        L.addWidget(self.lbl_low,   0,0)
        L.addWidget(self.indicator, 0,1, 1,6)
        L.addWidget(self.lbl_high,  0,7)

        # row 2: controls
        L.addWidget(self.ctl_decr,   1,1)
        L.addWidget(self.ctl_manual, 1,3, 1,1)
        L.addWidget(self.ctl_incr,   1,6)

        # row 3: multiknob name control
        L.addWidget(lbl_name,        2,2)
        L.addWidget(self.set_mkname, 2,3, 1,3)

        # row 4-5: step size control
        L.addWidget(lbl_step,        3,2)
        L.addWidget(self.set_step,   3,3, 1,1)
        L.addWidget(lbl_lims,        4,2)
        L.addWidget(self.set_lim_lo, 4,3, 1,1)
        L.addWidget(self.set_lim_hi, 4,4, 1,1)

        L.setSpacing(5)
        L.setContentsMargins(0,0,0,0)
        self.setLayout(L)
        return


    def reinit(self): self.mkname = self.set_mkname.text()

    @property
    def mkname(self): return self._mkname

    @mkname.setter
    def mkname(self, value):
        self._mkname = value
        self.displacement = 0.0
        self.set_mkname.setText(value)
        self.set_step.setText(f'{DEFAULT_STEP_SIZE:.2f}')
        self.set_lim_lo.setText(f'{KNOB_LOW:.2f}')
        self.set_lim_hi.setText(f'{KNOB_HIGH:.2f}')
        self.update_readbacks()
    
    @property
    def step_size(self): return float(self.set_step.text())

    @property
    def lim_lo(self): return float(self.set_lim_lo.text())
    
    @property
    def lim_hi(self): return float(self.set_lim_hi.text())

    def incr(self): self.update(self.step_size)

    def decr(self): self.update(-1 * self.step_size)   

    def update_manual(self):
        """ adjust knob value by the delta implied by the entered text """
        self.update(float(self.ctl_manual.text()) - self.displacement)

    def update(self, delta):
        """ write & track knob delta """
        self.displacement += delta
        set_mkb(self.mkname, delta)
        self.update_readbacks()

    def update_readbacks(self, **kw):
        self.ctl_manual.setText(f'{self.displacement:.1f}')
        self.indicator.setValue(int(self.displacement))

    def update_limits(self):
        lo = float(self.set_lim_lo.text())
        hi = float(self.set_lim_hi.text())
        if lo > hi:
            self.set_lim_lo.setText(hi)
            self.set_lim_hi.setText(lo)
        self.indicator.setMinimum(int(self.lim_lo))
        self.indicator.setMaximum(int(self.lim_hi))
        self.lim_lo.setText(self.lim_lo)
        self.lim_hi.setText(self.lim_hi)

