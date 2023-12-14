from PyQt5.QtCore import Qt
from pydm.widgets.label import PyDMLabel

PV_FB_TEMPLATE = '{}:FBCK:26:HSTA'

# stupid awful gross magic numbers
# temporary kludge, until HSTA bits can be decoded properly
HSTA_FBCK_ON = 268601505
HSTA_FBCK_COMP = 268599457

class F2SteeringFeedbackIndicator(PyDMLabel):
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