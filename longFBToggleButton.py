from epics import caget, caput
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QPushButton
from pydm.widgets.byte import PyDMByteIndicator
from pydm.widgets.channel import PyDMChannel

# matlab PV for feedback control -- single word, each bit controls a given FB
# the BIT_INDICES dict maps feedback names to bits
PV_FB_CONTROL = 'SIOC:SYS1:ML00:AO856'
BIT_INDICES = {
    'DL10E':  0,
    'BC11E':  2,
    'BC11BL': 3,
    'BC14E':  1,
    'BC14BL': 5,
    'BC20E':  4,
    }


class longFBToggleButton(QFrame):
    """
    subclass to make a toggle button for F2 feedback controls
    needs to set single bits of an overall status word
    """

    def __init__(self, FB_name, parent=None, args=None):
        QFrame.__init__(self, parent=parent)
        self.FB_name = FB_name
        self.bit = BIT_INDICES[FB_name]
        self.toggle_on = QPushButton('ON')
        self.toggle_off = QPushButton('OFF')
        self.status = PyDMByteIndicator()

        self.FB_state = PyDMChannel(
            address=PV_FB_CONTROL, value_slot=self.set_button_enable_states
            )
        self.FB_state.connect()

        self.toggle_on.clicked.connect(self.enable)
        self.toggle_off.clicked.connect(self.disable)

        self.toggle_on.setFixedWidth(50)
        self.toggle_off.setFixedWidth(50)

        L = QHBoxLayout()
        L.addWidget(self.toggle_on)
        L.addWidget(self.toggle_off)
        L.setSpacing(1)
        L.setContentsMargins(2,2,2,2)
        self.setLayout(L)

    def enable(self):
        init_ctrl_state = int(caget(PV_FB_CONTROL))
        new_ctrl_state = init_ctrl_state | (1 << self.bit)
        caput(PV_FB_CONTROL, new_ctrl_state)

    def disable(self):
        init_ctrl_state = int(caget(PV_FB_CONTROL))
        new_ctrl_state = init_ctrl_state & ~(1 << self.bit)
        caput(PV_FB_CONTROL, new_ctrl_state)

    def set_button_enable_states(self, new_value):
        feedback_on = (int(abs(new_value)) >> (self.bit)) & 1
        self.toggle_on.setDown(feedback_on)
        self.toggle_off.setDown(not feedback_on)