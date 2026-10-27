"""Static liquid-glass chrome for the chat window and dialogs.

Same idea as the orb (see lens.py) but the panel itself never animates: the
background behind the window is re-sampled only when the window moves/resizes
or the pixels behind it actually change (e.g. a video playing), so the glass
"reacts" without wobbling. If refraction isn't available (old Windows, capture
fails, or disabled in settings) the panel paints a plain dark rounded rect.
"""
from __future__ import annotations

import logging

import numpy as np
from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .lens import GlassPanelRenderer, exclude_from_capture

MARGIN = 12               # transparent margin around the panel (also gives the bezel room to sample)
RADIUS = 18
log = logging.getLogger("crystal")


class GlassPanel(QWidget):
    """Paints the pre-rendered glass image; falls back to a flat dark panel."""
    def __init__(self):
        super().__init__(); self.glass: QImage | None = None

    def set_glass(self, img: QImage | None):
        self.glass = img; self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        if self.glass is not None:
            p.drawImage(0, 0, self.glass)
        else:
            p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor(135, 190, 255, 110), 1))
            p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), RADIUS, RADIUS)
        p.end()


class GlassBackdrop(QObject):
    """Keeps a GlassPanel's glass image in sync with the desktop behind its window."""
    def __init__(self, window: QWidget, panel: GlassPanel, enabled: bool = True):
        super().__init__(window)
        self.win, self.panel = window, panel
        self.renderer = GlassPanelRenderer(radius=RADIUS)
        self.ok = None            # None = not tried yet, True/False after first show
        self.enabled = enabled
        self.sig = None
        self.timer = QTimer(self); self.timer.setInterval(100); self.timer.timeout.connect(self.refresh)
        window.installEventFilter(self)

    def _start_capture(self):
        if self.ok is None:
            self.ok = bool(self.enabled and exclude_from_capture(int(self.win.winId())))
            if not self.ok and self.enabled:
                log.info("Glass panel: refraction unavailable for %s, using flat panel", type(self.win).__name__)
        if self.ok:
            self.sig = None
            self.timer.start()
            QTimer.singleShot(0, self.refresh)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if not enabled:
            self.ok = False
            self.timer.stop()
            self.panel.set_glass(None)
        else:
            self.ok = None
            if self.win.isVisible():
                self._start_capture()

    def eventFilter(self, obj, ev):
        if obj is self.win:
            t = ev.type()
            if t == QEvent.Show:
                self._start_capture()
            elif t == QEvent.Hide:
                self.timer.stop()
            elif t in (QEvent.Move, QEvent.Resize):
                self.sig = None
        return False

    def _grab(self):
        win = self.win; dpr = win.devicePixelRatioF()
        W, H = int(round(win.width() * dpr)), int(round(win.height() * dpr))
        scr = win.screen(); geo = scr.geometry(); tl = win.mapToGlobal(QPoint(0, 0))
        pix = scr.grabWindow(0, tl.x() - geo.x(), tl.y() - geo.y(), win.width(), win.height())
        if pix.isNull(): return None
        img = pix.toImage().convertToFormat(QImage.Format_RGB32)
        if img.width() != W or img.height() != H:
            img = img.scaled(W, H, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        buf = np.frombuffer(img.constBits(), np.uint8).reshape(H, img.bytesPerLine() // 4, 4)
        return np.ascontiguousarray(buf[:, :W, :3]), dpr, (tl.x(), tl.y(), win.width(), win.height())  # copy while img is alive

    def refresh(self):
        if not self.ok or not self.win.isVisible(): return
        try:
            got = self._grab()
            if got is None: return
            frame, dpr, geom = got
            sig = (geom, hash(frame[::6, ::6].tobytes()))  # cheap "did anything change?" check
            if sig == self.sig: return
            self.sig = sig
            pr = self.panel.geometry()
            ox, oy = int(round(pr.x() * dpr)), int(round(pr.y() * dpr))
            pw, ph = int(round(pr.width() * dpr)), int(round(pr.height() * dpr))
            if pw < 40 or ph < 40 or ox + pw > frame.shape[1] or oy + ph > frame.shape[0]: return
            self.renderer.configure(ox, oy, pw, ph, dpr)
            out = self.renderer.render(frame)
            img = QImage(out.data, pw, ph, pw * 4, QImage.Format_ARGB32_Premultiplied).copy()  # deep copy: `out` is recycled
            img.setDevicePixelRatio(dpr); self.panel.set_glass(img)
        except Exception:
            log.exception("Glass panel render failed; switching to flat panel")
            self.ok = False; self.timer.stop(); self.panel.set_glass(None)


class DragLabel(QLabel):
    """A label you can grab to move its frameless window."""
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.window().windowHandle() is not None:
            self.window().windowHandle().startSystemMove()


class GlassDialog(QDialog):
    """Frameless glass dialog with a draggable title bar and close button.
    Subclasses add their widgets to `self.body_layout`."""
    def __init__(self, title: str, width: int, height: int, enabled: bool = True, flags=None):
        super().__init__()
        self.setObjectName("glass"); self.setWindowTitle(title.title())
        self.setWindowFlags(flags if flags is not None else Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.resize(width, height)
        outer = QVBoxLayout(self); outer.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        self.panel = GlassPanel(); self.panel.setObjectName("panel"); outer.addWidget(self.panel)
        pl = QVBoxLayout(self.panel); pl.setContentsMargins(16, 12, 16, 14); pl.setSpacing(8)
        bar = QHBoxLayout(); lbl = DragLabel(title); lbl.setObjectName("title"); bar.addWidget(lbl, 1)
        close = QPushButton("✕"); close.setFixedSize(30, 26); close.setToolTip("Close"); close.clicked.connect(self.reject); bar.addWidget(close)
        pl.addLayout(bar)
        self.body_layout = QVBoxLayout(); self.body_layout.setSpacing(8); pl.addLayout(self.body_layout, 1)
        self._backdrop = GlassBackdrop(self, self.panel, enabled)

    def set_glass_enabled(self, enabled: bool):
        self._backdrop.set_enabled(enabled)
