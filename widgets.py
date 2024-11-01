# pydm widgets for F2 GUIs

# =============================================================================

import os
import sys
import numpy as np
from PyQt5.QtCore import Qt
from pydm.widgets.label import PyDMLabel

from epics import caget, caput
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QPushButton
from pydm.widgets.byte import PyDMByteIndicator
from pydm.widgets.channel import PyDMChannel

from p4p.client.thread import Context
from p4p.nt import NTURI
SELF_PATH = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(*os.path.split(SELF_PATH)[:-1])
sys.path.append(REPO_ROOT)
from F2_pytools import slc_klys as slck
# import slc_klys as slck

STYLE_TEXT_GREEN = """
color: rgb(0,255,0);
"""

STYLE_TEXT_RED = """
color: rgb(255,0,0);
"""

STYLE_TEXT_WHITE = """
color: rgb(255,255,255);
"""

STYLE_BRD_GREEN = """
QFrame{
border-color: rgb(80,255,120);
border-width: 2px;
border-style: solid;
}
"""

STYLE_BRD_YELLOW = """
QFrame{
border-color: rgb(255,255,0);;
border-width: 2px;
border-style: solid;
}
"""

STYLE_BRD_CYAN = """
QFrame{
border-color: color: rgb(0,255,255);
border-width: 2px;
border-style: solid;
}
"""

PV_LONG_FB_CONTROL = 'SIOC:SYS1:ML00:AO856'
PV_LONG_FB_STATUS  = 'SIOC:SYS1:ML00:AO859'
I_DL10E  = 0
I_BC11E  = 2
I_BC11BL = 3
I_BC14E  = 1
I_BC14BL = 5
I_BC20E  = 4

PV_FB_TEMPLATE = 'FBCK:{}:{}:HSTA'
PV_FB_TEMPLATE_SLC = '{}:FBCK:{}:HSTA'

# HSTA bit index for on/off control of SCP transverse feedbacks
I_XFB_CONTROL = 11
RTYPE = NTURI([('TYPE','s')])
WTYPE = NTURI([('VALUE','d'), ('VALUE_TYPE','s')])

# stupid awful gross magic numbers
HSTA_FBCK_ON = 268601505
HSTA_FBCK_COMP = 268599457


class SCPSteeringIndicator(PyDMLabel):
    """ checks FBCK hardware status to check for feedback enable/compute """

    def __init__(self, FB_name, parent=None, args=None):
        init_channel = PV_FB_TEMPLATE.format(FB_name)
        PyDMLabel.__init__(self, init_channel=init_channel, parent=parent)
        self.FB_name = FB_name
        self.setAlignment(Qt.AlignCenter)

    def value_changed(self, new_value):
        PyDMLabel.value_changed(self, new_value)
        if new_value == HSTA_FBCK_ON:    
            self.setText('Enabled')
            self.setStyleSheet(STYLE_GREEN)
        elif new_value == HSTA_FBCK_COMP:
            self.setText('Compute')
            self.setStyleSheet(STYLE_YELLOW)
        else:                            
            self.setText('Off/Sample')

class SCPSteeringToggleButton(QFrame):
    """
    subclass to make a toggle button for F2 feedback controls
    needs to set single bits of an overall status word
    """

    def __init__(self, micro, parent=None, args=None):
        QFrame.__init__(self, parent=parent)

        assert micro in ('LI11', 'LI18')
        unit = 26
        if micro == 'LI18': unit = 28
        self.channel = PV_FB_TEMPLATE.format(micro, unit)

        # AIDA-PVA for writing, CA monitor for watching on/off state
        self.ctx = Context('pva')
        self.FB_state = PyDMChannel(address=PV_FB_TEMPLATE_SLC.format(micro, unit),
            value_slot=self.set_enable_states)
        self.FB_state.connect()

        self.toggle_on = QPushButton('ON')
        self.toggle_off = QPushButton('OFF')
        self.toggle_on.clicked.connect(self.enable_fb)
        self.toggle_off.clicked.connect(self.disable_fb)

        L = QHBoxLayout()
        L.addWidget(self.toggle_on)
        L.addWidget(self.toggle_off)
        L.setSpacing(1)
        L.setContentsMargins(0,0,0,0)
        self.setLayout(L)

    def get_fb_stat(self):
        readcall = RTYPE.wrap(
            scheme='pva', path=self.channel, kws={'TYPE':'INTEGER'}
            )
        res = self.ctx.rpc(self.channel, readcall, timeout=5.0)
        return res.raw.value

    def set_fb_stat(self, enable=True):
        init_state = self.get_fb_stat()

        if enable:
            new_state = init_state | (1 << I_XFB_CONTROL)
        else:
            new_state = init_state & ~(1 << I_XFB_CONTROL)

        writecall = WTYPE.wrap(
            scheme='pva', path=self.channel,
            kws={'VALUE':int(new_state), 'VALUE_TYPE':'INTEGER_ARRAY'}
            )
        res = self.ctx.rpc(self.channel, writecall, timeout=5.0)
        return res.raw.value

    def enable_fb(self): self.set_fb_stat(enable=True)

    def disable_fb(self): self.set_fb_stat(enable=False)

    def set_enable_states(self, new_value):
        feedback_on = (new_value == HSTA_FBCK_ON)

        on_style = STYLE_TEXT_GREEN if feedback_on else STYLE_TEXT_WHITE
        off_style = STYLE_TEXT_RED if not feedback_on else STYLE_TEXT_WHITE

        border = STYLE_BRD_GREEN if feedback_on else STYLE_BRD_RED
        self.setStyleSheet(border)

        self.toggle_on.setDown(feedback_on)
        self.toggle_on.setEnabled(not feedback_on)
        self.toggle_on.setStyleSheet(on_style)

        self.toggle_off.setDown(not feedback_on)
        self.toggle_off.setEnabled(feedback_on)
        self.toggle_off.setStyleSheet(off_style)


class F2LongFBToggleButton(QFrame):
    """
    subclass to make a toggle button for F2 feedback controls
    needs to set single bits of an overall status word
    """

    def __init__(self, bit_ID, parent=None, args=None):
        QFrame.__init__(self, parent=parent)
        self.bit = bit_ID
        self.toggle_on = QPushButton('ON')
        self.toggle_off = QPushButton('OFF')

        self.setStyleSheet(STYLE_BRD_GREEN)

        self.FB_state = PyDMChannel(address=PV_LONG_FB_CONTROL,
            value_slot=self.set_button_enable_states)
        self.FB_state.connect()

        self.toggle_on.clicked.connect(self.enable_fb)
        self.toggle_off.clicked.connect(self.disable_fb)

        self.toggle_on.setFixedWidth(50)
        self.toggle_off.setFixedWidth(50)

        L = QHBoxLayout()
        L.addWidget(self.toggle_on)
        L.addWidget(self.toggle_off)
        L.setSpacing(1)
        L.setContentsMargins(0,0,0,0)
        self.setLayout(L)

    def enable_fb(self):
        init_ctrl_state = int(caget(PV_LONG_FB_CONTROL))
        new_ctrl_state = init_ctrl_state | (1 << self.bit)
        caput(PV_LONG_FB_CONTROL, new_ctrl_state)

    def disable_fb(self):
        init_ctrl_state = int(caget(PV_LONG_FB_CONTROL))
        new_ctrl_state = init_ctrl_state & ~(1 << self.bit)
        caput(PV_LONG_FB_CONTROL, new_ctrl_state)

    def set_button_enable_states(self, new_value):
        feedback_on = (int(abs(new_value)) >> (self.bit)) & 1

        on_style = STYLE_TEXT_GREEN if feedback_on else STYLE_TEXT_WHITE
        off_style = STYLE_TEXT_RED if not feedback_on else STYLE_TEXT_WHITE

        border = STYLE_BRD_GREEN if feedback_on else STYLE_BRD_RED
        self.setStyleSheet(border)

        self.toggle_on.setDown(feedback_on)
        self.toggle_on.setEnabled(not feedback_on)
        self.toggle_on.setStyleSheet(on_style)

        self.toggle_off.setDown(not feedback_on)
        self.toggle_off.setEnabled(feedback_on)
        self.toggle_off.setStyleSheet(off_style)


class F2KlysToggleButton(QFrame):

    def __init__(self, klys_name, parent=None, args=None):
        QFrame.__init__(self, parent=parent)
        self.toggle_on = QPushButton('REACT')
        self.toggle_off = QPushButton('DEACT')
        self.kname = klys_name

        self.setStyleSheet(STYLE_BRD_GREEN)

        self.toggle_on.clicked.connect(self.react)
        self.toggle_off.clicked.connect(self.deact)

        L = QVBoxLayout()
        L.addWidget(self.toggle_on)
        L.addWidget(self.toggle_off)
        L.setSpacing(1)
        L.setContentsMargins(0,0,0,0)
        self.setLayout(L)
        return

    def react(self):
        slck.react(self.kname)
        self.set_button_enable_states(onbeam=True)
        return

    def deact(self):
        slck.deact(self.kname)
        self.set_button_enable_states(onbeam=False)
        return

    def set_button_enable_states(self, onbeam=True, maint=False):
        if maint:
            self.setStyleSheet(STYLE_BRD_CYAN)
            self.setEnabled(False)
            self.setGraphicsEffect(QGraphicsOpacityEffect(opacity=0.5))
            return
        else:
            self.setEnabled(True)

        border = STYLE_BRD_GREEN if onbeam else STYLE_BRD_YELLOW
        self.setStyleSheet(border)

        self.toggle_on.setDown(onbeam)
        self.toggle_on.setEnabled(not onbeam)

        self.toggle_off.setDown(not onbeam)
        self.toggle_off.setEnabled(onbeam)

