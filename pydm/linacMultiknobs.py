import os
import sys
from functools import partial
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QFrame, QGridLayout, QPushButton, QLineEdit, QSlider, QLabel
from epics import get_pv

# from aida.mkb import set_mkb
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

PHASE_LOW = -60
PHASE_HIGH = 0

# default increment in degS
DEFAULT_STEP_SIZE = 0.5

REFRESH_MS = 1000

class l2PhaseController(QFrame):
    """ L2 phase knob, can click to increment/decrement or type deltas """

    def __init__(self, parent=None, args=None):
        QFrame.__init__(self, parent=parent)

        self.mkname = 'l2_phase' # l2 phase multiknob for SB12/13/14
        self.displacement = 0.0  # total delta since initialization

        self.ctl_incr = QPushButton('+')
        self.ctl_decr = QPushButton('-')
        self.ctl_manual = QLineEdit('0.0')
        self.set_step = QLineEdit(f'{DEFAULT_STEP_SIZE:.2f}')

        # enforces numeric input
        self.ctl_manual.setValidator(QDoubleValidator(-180.0, 180.0, 2))
        self.set_step.setValidator(QDoubleValidator(0.0, 10.0, 2))

        self.l2_des_rbv = QLabel()
        self.l2_act_rbv = QLabel()
        self.l2_indicator = QSlider(Qt.Horizontal)

        lbl_des = QLabel("L2 PDES")
        lbl_act = QLabel("/ PACT")
        lbl_low = QLabel(str(PHASE_LOW))
        lbl_high = QLabel(str(PHASE_HIGH))

        self.ctl_decr.setMaximumWidth(40)
        self.ctl_incr.setMaximumWidth(40)

        lbl_step = QLabel("step:")

        self.l2_des_rbv.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.l2_act_rbv.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.l2_des_rbv.setMaximumHeight(24)
        self.l2_act_rbv.setMaximumHeight(24)
        self.l2_des_rbv.setMaximumWidth(60)
        self.l2_act_rbv.setMaximumWidth(60)
        self.l2_des_rbv.setMinimumWidth(60)
        self.l2_act_rbv.setMinimumWidth(60)
        self.l2_des_rbv.setStyleSheet(STYLE_BRD_BLK)

        lbl_des.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        lbl_act.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        lbl_des.setMaximumHeight(24)
        lbl_act.setMaximumHeight(24)

        lbl_step.setMaximumWidth(80)
        self.set_step.setMaximumWidth(80)

        lbl_low.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        lbl_high.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

        lbl_low.setMaximumWidth(30)
        lbl_high.setMaximumWidth(30)

        self.l2_indicator.setEnabled(False) # slider is not interactive

        self.l2_indicator.setMaximum(PHASE_HIGH)
        self.l2_indicator.setMinimum(PHASE_LOW)
        self.l2_indicator.setTickInterval(5)
        self.l2_indicator.setTickPosition(QSlider.TicksBelow)
        self.l2_indicator.setInvertedAppearance(True)

        self.PVs = {
            'des': [
                get_pv('LI12:SBST:1:PDES'),
                get_pv('LI13:SBST:1:PDES'),
                get_pv('LI14:SBST:1:PDES'),
                ],
            'act': [
                get_pv('LI12:SBST:1:PHAS'),
                get_pv('LI13:SBST:1:PHAS'),
                get_pv('LI14:SBST:1:PHAS'),
                ],
            }

        self.ctl_incr.clicked.connect(self.incr)
        self.ctl_decr.clicked.connect(self.decr)
        self.ctl_manual.returnPressed.connect(self.update_phase_manual)

        L = QGridLayout()

        # 1st & 2nd row: pdes/pact readbacks
        L.addWidget(lbl_des, 0,3)
        L.addWidget(lbl_act, 0,4)
        L.addWidget(self.l2_des_rbv, 1,3)
        L.addWidget(self.l2_act_rbv, 1,4)

        # row 3: slider readback
        L.addWidget(lbl_low, 2,0)
        L.addWidget(self.l2_indicator, 2,1, 1,6)
        L.addWidget(lbl_high, 2,7)

        # row 4: controls
        L.addWidget(self.ctl_decr,   3,1)
        L.addWidget(self.ctl_manual, 3,3, 1,2)
        L.addWidget(self.ctl_incr,   3,6)

        # row 5: step size control
        L.addWidget(lbl_step, 4,3)
        L.addWidget(self.set_step, 4,4)

        L.setSpacing(5)
        L.setContentsMargins(0,0,0,0)
        self.setLayout(L)

        self.update_readbacks()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.start()
        self.refresh_timer.setInterval(REFRESH_MS)
        self.refresh_timer.timeout.connect(self.update_readbacks)
        return

    @property
    def step_size(self): return float(self.set_step.text())

    @property
    def l2_pdes(self): return sum([pv.get() for pv in self.PVs['des']]) / 3.0

    @property
    def l2_pact(self): return sum([pv.get() for pv in self.PVs['act']]) / 3.0

    @property
    def phase_err(self): return self.l2_pdes - self.l2_pact

    def incr(self): self.update_phase(self.step_size)

    def decr(self): self.update_phase(-1 * self.step_size)   

    # moves the multiknob by the delta from the entered text
    def update_phase_manual(self): self.update_phase(float(self.ctl_manual.text()) - self.displacement)

    def update_phase(self, delta):
        """ writes & tracks phase delta """
        self.displacement += delta
        set_mkb(self.mkname, delta)
        self.update_readbacks()

    def reset(self): self.update_phase(-1 * self.displacement)

    def update_readbacks(self, **kw):
        self.ctl_manual.setText(f'{self.displacement:.1f}')
        self.l2_des_rbv.setText(f'{self.l2_pdes:.1f}')
        self.l2_act_rbv.setText(f'{self.l2_pact:.1f}')
        style = STYLE_BRD_GREEN
        if self.phase_err > 1.0: style = STYLE_BRD_RED
        self.l2_act_rbv.setStyleSheet(style)
        self.l2_indicator.setValue(int(PHASE_LOW - self.l2_pdes))
