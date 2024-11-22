from pydm import Display
from linacMultiknobs import l2PhaseController

class l2PhaseKnob(Display):
    def __init__(self, parent=None, args=None):
        Display.__init__(self, parent=parent, args=args)
        ctl = l2PhaseController()
        self.ui.layout().addWidget(ctl)

    def ui_filename(self): return 'l2_phase_knob.ui'
