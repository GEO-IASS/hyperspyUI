from hyperspyui.plugins.plugin import Plugin
from hyperspy.hspy import *


class Tightlayout(Plugin):
    name = "TightLayout"

    def create_actions(self):
        self.add_action(
            self.name + '.default', "Tight layout", self.default,
            icon="move.svg",
            tip="Apply a tight layout to all plots of selected signal.")

    def create_menu(self):
        self.add_menuitem('Plot', self.ui.actions[self.name + '.default'])

    def create_toolbars(self):
        self.add_toolbar_button(
            'Plot',
            self.ui.actions[
                self.name +
                '.default'])

    def default(self):
        ui = self.ui
        s = ui.get_selected_signal()
        for p in (s._plot.signal_plot, s._plot.navigator_plot):
            p.figure.tight_layout()
            p.figure.canvas.draw()
