from hyperspyui.plugins.plugin import Plugin
from hyperspy.signal import Signal
import numpy as np
from hyperspy.signals import Spectrum, Image
from hyperspyui.tools import MultiSelectionTool
from hyperspyui.util import win2sig
from hyperspy.misc.rgb_tools import regular_array2rgbx

import matplotlib.cm as plt_cm

# TODO: Add dialog for manual editing of ROIs + Preview checkbox.


class Segmentation(Plugin):
    name = "Segmentation"

    def create_tools(self):
        self.tool = MultiSelectionTool()
        self.tool.name = 'Segmentation tool'
        self.tool.updated[Signal, list].connect(self._on_update)
        self.tool.accepted[Signal, list].connect(self.segment)
        self.tool.validator = self._tool_signal_validator
        self.add_tool(self.tool, self._select_image)
        self.map = {}
        self.ui.actions[self.tool.name].triggered.connect(
            lambda c: self.start())

    def _select_image(self, win, action):
        """Signal selection callback for actions that are only valid for
        selected Signals.
        """
        sw = win2sig(win, self.ui.signals, self.ui._plotting_signal)
        if sw is None or not sw.signal.axes_manager.signal_dimension == 2:
            action.setEnabled(False)
        else:
            action.setEnabled(True)

    def _tool_signal_validator(self, signal, axes):
        if not self.tool._default_validator(signal, axes):
            return False
        return signal in self.map

    def start(self, signal=None):
        if signal is None:
            signal = self.ui.get_selected_signal()
        data = signal()
        hist = signal._get_signal_signal(data).get_histogram(1000)
        hist.plot()

        s_out = Spectrum(self._make_gray(data))
        s_out.change_dtype('rgb8')
        s_out.plot()

        self.map[hist] = (signal, s_out)

    def _make_gray(self, data):
        data = data - np.nanmin(data)
        data /= np.nanmax(data)
        return (255 * plt_cm.gray(data)).astype('uint8')

    def segment(self, signal, rois):
        if signal is None:
            signal = self.ui.get_selected_signal()

        if signal in self.map:
            histogram = signal
            source, s_out = self.map[signal]
        else:
            found = False
            for h, (s, s_out) in self.map.iteritems():
                if signal in (s, s_out):
                    found = True
                    histogram = h
                    source = s
                    break
            if not found:
                histogram = None
                s_out = None
                source = signal
        if histogram is not None:
            self.ui.lut_signalwrapper[histogram].close()
        if s_out is not None:
            self.ui.lut_signalwrapper[s_out].close()

        N = len(rois)
        if N <= 256:
            dtype = np.uint8
        elif N <= 2**16:
            dtype = np.uint16
        else:
            dtype = np.uint32
        src_data = source()
        data = np.zeros(src_data.shape, dtype)
        data[...] = np.nan
        for i, r in enumerate(rois):
            # Checks has to be inclusive to catch edges
            mask = (src_data <= r.right) & (src_data >= r.left)
            data[mask] = i + 1

        s_seg = Image(data)
        s_seg.plot(cmap=plt_cm.jet)

        roi_str = '[' + ',\n'.join([str(r) for r in rois]) + ']'
        self.record_code('segment_rois = ' + roi_str)
        self.record_code('<p>.segment(None, segment_rois)')

    def _on_update(self, histogram, rois):
        if histogram not in self.map:
            return
        source, s_out = self.map[histogram]
        N = len(rois)
        data = source()

        gray = self._make_gray(data)
        s_out.data = regular_array2rgbx(gray)
        for i in xrange(N):
            color = (255 * plt_cm.hsv([float(i) / max(N, 10)])).astype('uint8')
            color = regular_array2rgbx(color)
            r = rois[i]
            mask = (data < r.right) & (data >= r.left)
            s_out.data[mask] = color
        s_out.update_plot()