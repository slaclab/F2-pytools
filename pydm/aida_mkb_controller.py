from pydm import Display
from aida_mkb import AIDAMKBController

class GenericAIDAMKB(Display):
    def __init__(self, parent=None, args=None):
        Display.__init__(self, parent=parent, args=args)
        self.ui.body.layout().addWidget(AIDAMKBController('s20_energy_4and5'))

    def ui_filename(self): return 'l2_phase_knob.ui'
