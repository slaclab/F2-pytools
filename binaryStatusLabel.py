from pydm.widgets.label import PyDMLabel
from PyQt5.QtCore import Qt

STYLE_HIVIS_ON = """
background-color: rgb(0, 255, 0);
color: rgb(0, 0, 0);
"""

STYLE_HIVIS_OFF = """
background-color: rgb(255, 0, 0);
color: rgb(255, 255, 255);
"""

class binaryStatusLabel(PyDMLabel):
    """
    PyDMLabel subclass to display text based on a status bit
    Basically a PyDMByteIndicator but with superimposed text
    """

    def __init__(self, channel, bit=0, parent=None, args=None):
        super(bitStatusLabel, self).__init__(parent=parent)

        self.channel = channel
        self.bit = bit
        self.text_on = 'ON'
        self.text_off = 'OFF'

        # set bold text, center text alignment
        self.setAlignment(Qt.AlignCenter)
        self.setFont(STATUS_FONT)

    def value_changed(self, new_value):
        """
        slot for PV value changes
        """
        super(bitStatusLabel, self).value_changed(new_value)

        # extract the desired bit
        on_state = (int(abs(new_value)) >> (self.bit)) & 1

        # set text and stylesheet accordingly
        style = STYLE_HIVIS_ON if on_state else STYLE_HIVIS_OFF
        text = self.text_on    if on_state else self.text_off

        self.setStyleSheet(style)
        self.setText(text)