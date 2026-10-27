from __future__ import annotations
import asyncio, logging, math, os, sys, time, uuid
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QRectF, QPoint, QRunnable, QThreadPool, Signal, QObject, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QLinearGradient, QPen, QBrush, QAction, QIcon, QFont, QImage
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFormLayout, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox,
    QListWidget, QFileDialog, QSystemTrayIcon, QMenu, QTabWidget, QMessageBox, QSlider, QGroupBox)
from ..config import Settings, APP_DIR
from ..agent import OllamaAgent
from ..history import recent, add, initialize
from ..tts import SpeechEngine, play_wav
from .glass import GlassDialog
from .lens import LensRenderer, exclude_from_capture

class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)
    log = Signal(str)

class Worker(QRunnable):
    def __init__(self, fn):
        super().__init__(); self.fn = fn; self.signals = WorkerSignals()
    def run(self):
        try: self.signals.result.emit(self.fn())
        except Exception as e: self.signals.error.emit(str(e))

class OrbWindow(QWidget):
    """Liquid-glass orb.

    Every frame it grabs the desktop pixels under itself and warps them through
    a lens (see lens.py), so it reacts to wallpapers, windows, images and video.
    The orb window is excluded from screen capture (Windows 10 2004+), which is
    what stops it from photographing itself. If that is unavailable, or a frame
    can't be captured, it falls back to the old painted glass orb.
    """
    def __init__(self, open_chat, settings: Settings, ctrl=None):
        super().__init__(); self.open_chat = open_chat; self.settings = settings; self.ctrl = ctrl; self.phase = 0.0; self.state = "idle"; self.drag_offset = None; self.press_global = None
        self.lens = None; self.lens_img = None; self._lens_buf = None; self._lens_tried = False; self._frame_ms = 0.0
        # Hold-to-speak detection
        self._press_time = 0.0
        self._hold_threshold_ms = 400   # press longer than this = voice input
        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.timeout.connect(self._on_hold)
        self._is_holding = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setFixedSize(settings.orb_size, settings.orb_size)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 38, screen.bottom() - self.height() - 90)
        self.timer = QTimer(self); self.timer.timeout.connect(self._tick); self.timer.start(33)
        self.setToolTip("Crystal Companion · click to chat · right-click for settings")

    # ---- lens setup -------------------------------------------------------
    def showEvent(self, e):
        super().showEvent(e)
        if not self._lens_tried:  # needs a real native window handle, so do it on first show
            self._lens_tried = True
            if getattr(self.settings, "orb_refraction", True) and exclude_from_capture(int(self.winId())):
                self.lens = LensRenderer(self._device_size(), wobble=getattr(self.settings, "orb_wobble", 1.0))
                logging.getLogger("crystal").info("Orb: live refraction enabled")
            else:
                logging.getLogger("crystal").warning("Orb: refraction unavailable, using painted glass fallback")

    def _device_size(self): return max(32, int(round(self.width() * self.devicePixelRatioF())))

    def _grab_frame(self):
        """Desktop pixels under the orb as an (n, n, 3) BGR numpy array, or None."""
        import numpy as np
        n = self._device_size(); scr = self.screen(); geo = scr.geometry(); tl = self.mapToGlobal(QPoint(0, 0))
        pix = scr.grabWindow(0, tl.x() - geo.x(), tl.y() - geo.y(), self.width(), self.height())
        if pix.isNull(): return None
        img = pix.toImage().convertToFormat(QImage.Format_RGB32)
        if img.width() != n or img.height() != n:
            img = img.scaled(n, n, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        buf = np.frombuffer(img.constBits(), np.uint8).reshape(n, img.bytesPerLine() // 4, 4)
        return buf[:, :n, :3].copy()  # BGRA -> BGR; keep pixels alive after the local QImage is released

    def _render_lens(self):
        import time
        t0 = time.perf_counter()
        n = self._device_size()
        if self.lens.n != n: self.lens.configure(n)
        frame = self._grab_frame()
        if frame is None: self.lens_img = None; return
        out = self.lens.render(frame, self.phase * 2.2, self.state)
        self._lens_buf = out  # keep the numpy buffer alive for the QImage
        img = QImage(out.data, n, n, n * 4, QImage.Format_ARGB32_Premultiplied)
        img.setDevicePixelRatio(self.devicePixelRatioF()); self.lens_img = img
        # adapt frame rate if this machine is slow
        self._frame_ms = self._frame_ms * .9 + (time.perf_counter() - t0) * 1000 * .1
        self.timer.setInterval(int(min(66, max(16, self._frame_ms * 1.6))))

    # ---- housekeeping -----------------------------------------------------
    def _tick(self):
        self.phase += .025
        if self.lens is not None:
            try: self._render_lens()
            except Exception: logging.getLogger("crystal").exception("Lens render failed; falling back"); self.lens = None; self.lens_img = None
        self.update()
    def set_state(self, state): self.state = state; self.update()
    def apply_settings(self, settings):
        self.settings = settings; self.setFixedSize(settings.orb_size, settings.orb_size)
        if self.lens is not None:
            self.lens.wobble = getattr(settings, "orb_wobble", 1.0); self.lens.configure(self._device_size())
        self.update()

    # ---- painting ---------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setOpacity(self.settings.orb_opacity)
        if self.lens_img is not None: p.drawImage(0, 0, self.lens_img)
        else: self._paint_procedural(p)
        p.end()

    def _paint_procedural(self, p):
        """Original painted-glass look (fallback when live refraction is unavailable)."""
        s = self.width(); r = s * .43; cx = cy = s / 2
        # Transparent fill lets the actual desktop remain visible through the sphere.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(120, 190, 255, 9)); p.drawEllipse(QRectF(cx-r, cy-r, 2*r, 2*r))
        # Layered radial gradients create the glass volume and cool edge caustics.
        g = QRadialGradient(cx-r*.30, cy-r*.38, r*1.55)
        g.setColorAt(0.0, QColor(255,255,255,26)); g.setColorAt(.24, QColor(105,180,255,12)); g.setColorAt(.63, QColor(90,100,255,9)); g.setColorAt(.88, QColor(30,220,255,24)); g.setColorAt(1, QColor(210,245,255,120))
        p.setBrush(QBrush(g)); p.drawEllipse(QRectF(cx-r,cy-r,2*r,2*r))
        # Animated internal rings / caustics.
        ring_color = QColor(130, 220, 255, 75 if self.state == "idle" else 145)
        p.setBrush(Qt.NoBrush); p.setPen(QPen(ring_color, 1.1))
        for i in range(3):
            rr = r*(.35 + i*.17) + math.sin(self.phase*1.7+i)*2.2
            p.drawEllipse(QRectF(cx-rr,cy-rr,2*rr,2*rr))
        # Highlights.
        p.setPen(Qt.NoPen); hg = QRadialGradient(cx-r*.38,cy-r*.48,r*.47)
        hg.setColorAt(0,QColor(255,255,255,155)); hg.setColorAt(.18,QColor(220,245,255,48)); hg.setColorAt(1,QColor(255,255,255,0))
        p.setBrush(hg); p.drawEllipse(QRectF(cx-r*.75,cy-r*.82,r*1.05,r*.82))
        # Lower refracted glint.
        lg = QLinearGradient(cx-r*.5,cy+r*.35,cx+r*.6,cy+r*.9)
        lg.setColorAt(0,QColor(0,220,255,0)); lg.setColorAt(.5,QColor(110,140,255,55)); lg.setColorAt(1,QColor(255,255,255,0))
        p.setBrush(lg); p.drawEllipse(QRectF(cx-r*.65,cy+r*.32,r*1.3,r*.36))
        # State indicator ring.
        col = {"idle": QColor(145,220,255,150), "thinking": QColor(190,135,255,230), "speaking": QColor(105,255,210,230), "error": QColor(255,100,120,230)}.get(self.state, QColor(145,220,255,150))
        p.setPen(QPen(col, 2.0)); p.setBrush(Qt.NoBrush); p.drawEllipse(QRectF(cx-r,cy-r,2*r,2*r))

    # ---- interaction -------------------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.press_global = e.globalPosition().toPoint(); self.drag_offset = self.press_global - self.frameGeometry().topLeft()
            self._press_time = time.perf_counter()
            self._hold_timer.start(self._hold_threshold_ms)
        elif e.button() == Qt.RightButton: self.open_chat(settings_only=True)
    def mouseMoveEvent(self, e):
        if self.drag_offset is not None and e.buttons() & Qt.LeftButton: self.move(e.globalPosition().toPoint()-self.drag_offset)
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._hold_timer.stop()
            elapsed_ms = (time.perf_counter() - self._press_time) * 1000
            if self.drag_offset is not None:
                delta = e.globalPosition().toPoint() - self.press_global
                self.drag_offset = None; self.press_global = None
                if delta.manhattanLength() < 5:
                    if elapsed_ms < self._hold_threshold_ms:
                        self.open_chat()   # short click → open chat
                    elif self._is_holding:
                        self._stop_voice_input()  # release after hold → process voice
        elif e.button() == Qt.RightButton: pass

    def _on_hold(self):
        """Triggered when the press exceeds the hold threshold."""
        self._is_holding = True
        self.state = "listening"
        self._start_voice_input()

    def _start_voice_input(self):
        """Begin listening for voice input using background STT."""
        self._subtitle_text("Listening…", hold_ms=60000)
        # Use background listening so we can stop when user releases the orb
        def run_stt():
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                mic = sr.Microphone()
                self._stt_result = None
                self._stt_error = None

                def callback(recognizer, audio):
                    try:
                        self._stt_result = recognizer.recognize_google(audio)
                    except Exception as e:
                        self._stt_error = str(e)

                with mic as source:
                    r.adjust_for_ambient_noise(source, duration=0.3)
                stop_listening = r.listen_in_background(mic, callback, phrase_time_limit=15)
                # Wait while user is holding the orb (up to 30s)
                import time as _t
                for _ in range(600):  # 600 * 50ms = 30s max
                    if not self._is_holding:
                        break
                    _t.sleep(0.05)
                stop_listening(wait_for_stop=False)
                if self._stt_result is not None:
                    return self._stt_result
                if self._stt_error:
                    raise RuntimeError(self._stt_error)
                raise RuntimeError("No speech detected before release.")
            except Exception as e:
                raise RuntimeError(f"Voice input failed: {e}")

        w = Worker(run_stt)
        w.signals.result.connect(self._on_voice_result)
        w.signals.error.connect(self._on_voice_error)
        self.ctrl.pool.start(w)

    def _stop_voice_input(self):
        """Stop listening and reset state."""
        self._is_holding = False
        self.state = "idle"

    def _on_voice_result(self, text: str):
        """Handle recognized speech: send as query (subtitle handled by _handle_voice_query)."""
        self._is_holding = False
        self.state = "idle"
        # Send the recognized text as a user query through the chat flow
        # _handle_voice_query will show the subtitle itself
        if self.ctrl is not None:
            self.ctrl.log.info("Voice recognized: %s", text)
            self.ctrl._handle_voice_query(text)

    def _on_voice_error(self, message: str):
        self._is_holding = False
        self.state = "idle"
        if self.ctrl is not None:
            self.ctrl.log.error("Voice input error: %s", message)
        self._subtitle_text(f"Voice error: {message}", hold_ms=3000)

    def _subtitle_text(self, text: str, hold_ms: int = 3000):
        """Show text in the subtitle window below the orb."""
        sub = self.ctrl.subtitle
        sub.bind_orb(self)
        sub.show_text(text, hold_ms=hold_ms)

class ChatWindow(GlassDialog):
    def __init__(self, app_controller):
        super().__init__(
            "CRYSTAL / LOCAL AGENT",
            440,
            390,
            enabled=app_controller.settings.glass_panels,
            flags=Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool,
        )
        self.ctrl = app_controller; self.session_id = str(uuid.uuid4()); self.busy = False
        pl = self.body_layout
        header = QHBoxLayout(); header.addStretch()
        self.status = QLabel("● READY"); self.status.setObjectName("status"); header.addWidget(self.status); pl.addLayout(header)
        self.transcript = QTextEdit(); self.transcript.setReadOnly(True); self.transcript.setObjectName("transcript"); self.transcript.setPlaceholderText("Your conversation stays on this device."); pl.addWidget(self.transcript,1)
        row = QHBoxLayout(); self.entry = QLineEdit(); self.entry.setPlaceholderText("Ask Crystal anything…  ↵"); self.entry.returnPressed.connect(self.send_query); row.addWidget(self.entry,1)
        self.send_btn = QPushButton("Send ↗"); self.send_btn.clicked.connect(self.send_query); row.addWidget(self.send_btn); pl.addLayout(row)
        foot = QHBoxLayout(); settings_btn = QPushButton("⚙ Settings"); settings_btn.clicked.connect(self.ctrl.open_settings); foot.addWidget(settings_btn)
        debug_btn = QPushButton("⌁ Diagnostics"); debug_btn.clicked.connect(self.ctrl.toggle_debug); foot.addWidget(debug_btn); foot.addStretch()
        clear_btn = QPushButton("Clear view"); clear_btn.clicked.connect(self.transcript.clear); foot.addWidget(clear_btn); pl.addLayout(foot)
        self.setStyleSheet(STYLE)
        self.entry.setFocus()
    def place_under_orb(self, orb):
        screen = QApplication.primaryScreen().availableGeometry(); x = orb.x()+orb.width()//2-self.width()//2; y=orb.y()+orb.height()+8
        if y+self.height()>screen.bottom(): y=orb.y()-self.height()-8
        self.move(max(screen.left(),min(x,screen.right()-self.width())), max(screen.top(),y))
    def append(self, who, text):
        safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
        color = "#86d8ff" if who == "YOU" else "#b9ffe7" if who == "CRYSTAL" else "#ff9ba8"
        self.transcript.append(f'<p><span style="color:{color};font-weight:700">{who}</span><br><span style="color:#e8efff">{safe}</span></p>')
    def send_query(self):
        if self.busy: return
        query = self.entry.text().strip()
        if not query: return
        self.entry.clear(); self.append("YOU",query); self.ctrl.log.info("User query submitted (%d chars)",len(query))
        self.busy=True; self.send_btn.setEnabled(False); self.status.setText("◌ THINKING"); self.ctrl.orb.set_state("thinking")
        old = recent(self.session_id) if self.ctrl.settings.remember_history else []
        worker = Worker(lambda: asyncio.run(self.ctrl.agent.ask(query,old,self.ctrl.settings)))
        worker.signals.result.connect(lambda answer: self.on_answer(query,answer))
        worker.signals.error.connect(self.on_error); self.ctrl.pool.start(worker)
    def on_answer(self, query, answer):
        self.append("CRYSTAL",answer); self.ctrl.log.info("Assistant response received (%d chars)",len(answer))
        if self.ctrl.settings.remember_history:
            add(self.session_id,"user",query); add(self.session_id,"assistant",answer)
        self.busy=False; self.send_btn.setEnabled(True); self.status.setText("● READY"); self.ctrl.orb.set_state("speaking" if self.ctrl.settings.tts_enabled else "idle")
        if self.ctrl.settings.tts_enabled:
            self.status.setText("♫ SPEAKING / LOADING TTS")
            w=Worker(lambda: self.ctrl.tts.synthesize(answer,self.ctrl.settings.tts_model,self.ctrl.settings.tts_speed,self.ctrl.settings.tts_device))
            w.signals.result.connect(self.play_audio); w.signals.error.connect(self.tts_error); self.ctrl.pool.start(w)
        else: self.ctrl.orb.set_state("idle")
    def play_audio(self, data):
        self.status.setText("♫ SPEAKING")
        w=Worker(lambda: play_wav(data,self.ctrl.log)); w.signals.result.connect(lambda _: self.finish_speech()); w.signals.error.connect(self.tts_error); self.ctrl.pool.start(w)
    def finish_speech(self): self.status.setText("● READY"); self.ctrl.orb.set_state("idle")
    def on_error(self, message):
        self.append("ERROR",message); self.ctrl.log.error("Agent request failed: %s",message)
        self.busy=False; self.send_btn.setEnabled(True); self.status.setText("! ERROR"); self.ctrl.orb.set_state("error")
    def tts_error(self,message):
        self.append("TTS ERROR",message); self.ctrl.log.error("TTS failed: %s",message); self.status.setText("● TEXT READY / TTS FAILED"); self.ctrl.orb.set_state("error")

class SettingsWindow(GlassDialog):
    saved = Signal(object)
    def __init__(self, settings: Settings, logger):
        super().__init__("Crystal Companion / Settings", 690, 650, enabled=settings.glass_panels)
        self.settings=settings; self.log=logger; self.setStyleSheet(STYLE)
        root=self.body_layout; tabs=QTabWidget(); root.addWidget(tabs)
        # Models tab
        models=QWidget(); form=QFormLayout(models)
        self.host=QLineEdit(settings.ollama_host); form.addRow("Ollama endpoint",self.host)
        self.fast=QLineEdit(settings.fast_model); form.addRow("Fast model",self.fast)
        self.reason=QLineEdit(settings.reasoning_model); form.addRow("Reasoning / mid-tier model",self.reason)
        self.use_reason=QCheckBox("Use reasoning model for all requests"); self.use_reason.setChecked(settings.use_reasoning_model); form.addRow("Routing",self.use_reason)
        self.temp=QDoubleSpinBox(); self.temp.setRange(0,2); self.temp.setSingleStep(.05); self.temp.setValue(settings.temperature); form.addRow("Temperature",self.temp)
        self.tokens=QSpinBox(); self.tokens.setRange(32,8192); self.tokens.setValue(settings.max_tokens); form.addRow("Maximum output tokens",self.tokens)
        self.tts_enabled=QCheckBox("Speak every assistant response"); self.tts_enabled.setChecked(settings.tts_enabled); form.addRow("Text-to-speech",self.tts_enabled)
        self.tts_model=QLineEdit(settings.tts_model); form.addRow("TTS Hugging Face model",self.tts_model)
        self.speed=QDoubleSpinBox(); self.speed.setRange(.5,2); self.speed.setSingleStep(.1); self.speed.setValue(settings.tts_speed); form.addRow("Speech speed",self.speed)
        self.device=QComboBox(); self.device.addItems(["auto","cpu","cuda:0"]); self.device.setCurrentText(settings.tts_device); form.addRow("TTS device map",self.device)
        tabs.addTab(models,"Models & Voice")
        # Folders tab
        files=QWidget(); fl=QVBoxLayout(files); self.folder_enable=QCheckBox("Allow read-only access to selected folders"); self.folder_enable.setChecked(settings.file_access_enabled); fl.addWidget(self.folder_enable)
        self.folders=QListWidget(); self.folders.addItems(settings.allowed_folders); fl.addWidget(self.folders,1)
        fr=QHBoxLayout(); addf=QPushButton("＋ Add folder"); addf.clicked.connect(self.add_folder); remf=QPushButton("Remove selected"); remf.clicked.connect(lambda: self.folders.takeItem(self.folders.currentRow()) if self.folders.currentRow()>=0 else None); fr.addWidget(addf); fr.addWidget(remf); fr.addStretch(); fl.addLayout(fr)
        note=QLabel("Safety: the agent can list filenames, search filenames, and read supported text files only. It cannot execute files or run shell commands."); note.setWordWrap(True); fl.addWidget(note); tabs.addTab(files,"Folder Access")
        # Appearance / behaviour
        ui=QWidget(); uf=QFormLayout(ui)
        self.size=QSpinBox(); self.size.setRange(100,360); self.size.setValue(settings.orb_size); uf.addRow("Orb diameter (px)",self.size)
        self.opacity=QDoubleSpinBox(); self.opacity.setRange(.2,1); self.opacity.setSingleStep(.05); self.opacity.setValue(settings.orb_opacity); uf.addRow("Orb opacity",self.opacity)
        self.history=QCheckBox("Persist conversation history locally"); self.history.setChecked(settings.remember_history); uf.addRow("History",self.history)
        self.startup=QCheckBox("Launch Crystal when I sign in to Windows"); self.startup.setChecked(settings.start_with_windows); uf.addRow("Startup",self.startup)
        self.debug=QCheckBox("Show live diagnostics panel"); self.debug.setChecked(settings.show_debug_panel); uf.addRow("Diagnostics",self.debug)
        self.glass_panels=QCheckBox("Use glass effect for chat and dialogs"); self.glass_panels.setChecked(settings.glass_panels); uf.addRow("Glass panels",self.glass_panels)
        self.speak_errors=QCheckBox("Speak errors aloud"); self.speak_errors.setChecked(settings.speak_errors); uf.addRow("Error behaviour",self.speak_errors)
        self.maxfile=QSpinBox(); self.maxfile.setRange(1,20); self.maxfile.setValue(settings.max_file_mb); uf.addRow("Maximum text file size (MB)",self.maxfile)
        self.context=QSpinBox(); self.context.setRange(1000,50000); self.context.setSingleStep(1000); self.context.setValue(settings.max_context_chars); uf.addRow("Maximum file context characters",self.context)
        self.loglevel=QComboBox(); self.loglevel.addItems(["DEBUG","INFO","WARNING","ERROR"]); self.loglevel.setCurrentText(settings.log_level); uf.addRow("Log level",self.loglevel)
        tabs.addTab(ui,"Appearance & Privacy")
        bottom=QHBoxLayout(); self.status=QLabel(f"Settings are stored in {APP_DIR / 'settings.json'}"); self.status.setWordWrap(True); bottom.addWidget(self.status,1)
        test=QPushButton("Test Ollama"); test.clicked.connect(self.test_ollama); bottom.addWidget(test)
        save=QPushButton("Save settings"); save.clicked.connect(self.save_settings); bottom.addWidget(save); root.addLayout(bottom)
    def add_folder(self):
        p=QFileDialog.getExistingDirectory(self,"Choose an allowed folder")
        if p and not [self.folders.item(i).text() for i in range(self.folders.count())].count(p): self.folders.addItem(p)
    def collect(self):
        s=self.settings
        s.ollama_host=self.host.text().strip().rstrip("/"); s.fast_model=self.fast.text().strip(); s.reasoning_model=self.reason.text().strip(); s.use_reasoning_model=self.use_reason.isChecked()
        s.temperature=self.temp.value(); s.max_tokens=self.tokens.value(); s.tts_enabled=self.tts_enabled.isChecked(); s.tts_model=self.tts_model.text().strip(); s.tts_speed=self.speed.value(); s.tts_device=self.device.currentText()
        s.allowed_folders=[self.folders.item(i).text() for i in range(self.folders.count())]; s.file_access_enabled=self.folder_enable.isChecked(); s.orb_size=self.size.value(); s.orb_opacity=self.opacity.value()
        s.remember_history=self.history.isChecked(); s.start_with_windows=self.startup.isChecked(); s.show_debug_panel=self.debug.isChecked(); s.glass_panels=self.glass_panels.isChecked(); s.speak_errors=self.speak_errors.isChecked(); s.max_file_mb=self.maxfile.value(); s.max_context_chars=self.context.value(); s.log_level=self.loglevel.currentText(); return s
    def save_settings(self):
        try:
            s=self.collect()
            if not s.ollama_host or not s.fast_model or not s.reasoning_model: raise ValueError("Ollama endpoint and both model names are required.")
            s.save(); self.log.info("Settings saved")
            try: self.set_windows_startup(s.start_with_windows)
            except Exception as startup_error: self.log.exception("Could not update Windows startup setting"); QMessageBox.warning(self,"Startup setting",str(startup_error))
            self.saved.emit(s); self.status.setText("Saved successfully.")
        except Exception as e: QMessageBox.critical(self,"Could not save settings",str(e))
    def set_windows_startup(self, enabled: bool):
        if sys.platform != "win32":
            if enabled: raise RuntimeError("Automatic sign-in startup is currently implemented for Windows only.")
            return
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                command = f'"{sys.executable}" -m crystal_agent'
                winreg.SetValueEx(key, "CrystalCompanion", 0, winreg.REG_SZ, command)
            else:
                try: winreg.DeleteValue(key, "CrystalCompanion")
                except FileNotFoundError: pass

    def test_ollama(self):
        host=self.host.text().strip().rstrip("/")
        def run():
            import httpx
            r=httpx.get(host+"/api/tags",timeout=5); r.raise_for_status(); return ", ".join(m.get("name","") for m in r.json().get("models",[])) or "Connected, but no models are installed."
        w=Worker(run); w.signals.result.connect(lambda x: QMessageBox.information(self,"Ollama connection",f"Connected. Installed models:\n{x}")); w.signals.error.connect(lambda x: QMessageBox.warning(self,"Ollama connection failed",x)); QThreadPool.globalInstance().start(w)

class DebugWindow(GlassDialog):
    def __init__(self, glass_enabled: bool = True):
        super().__init__("Crystal / Live diagnostics", 760, 380, enabled=glass_enabled)
        self.setStyleSheet(STYLE)
        lay=self.body_layout; self.text=QTextEdit(); self.text.setReadOnly(True); lay.addWidget(self.text)
        row=QHBoxLayout(); refresh=QPushButton("Refresh log"); refresh.clicked.connect(self.refresh); row.addWidget(refresh); openlog=QPushButton("Open log folder"); openlog.clicked.connect(lambda: os.startfile(str(APP_DIR)) if sys.platform=="win32" else None); row.addWidget(openlog); row.addStretch(); lay.addLayout(row)
        self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(1200); self.refresh()
    def refresh(self):
        p=APP_DIR/"crystal.log"
        try: data=p.read_text(encoding="utf-8",errors="replace")[-50000:]
        except Exception as e: data=f"Log not available yet: {e}"
        self.text.setPlainText(data); from PySide6.QtGui import QTextCursor
        self.text.moveCursor(QTextCursor.End)

class SubtitleWindow(GlassDialog):
    """Frameless glass subtitle widget shown below the orb.

    Displays fade-in/fade-out animated text for spoken input and assistant
    responses. Text stays visible until explicitly replaced or cleared.
    """

    def __init__(self, glass_enabled: bool = True):
        super().__init__("Crystal / Subtitles", 340, 90, enabled=glass_enabled)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )

        pl = self.body_layout
        self.label = QLabel()
        self.label.setObjectName("subtitle")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignCenter)
        pl.addWidget(self.label)

        # Opacity effect for fade in/out animation
        self._opacity = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)

        self._anim = QPropertyAnimation(self._opacity, b"opacity", self)
        self._anim.setDuration(350)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

        self.hide()

    def show_text(self, text: str, hold_ms: int = 4000):
        """Show `text` with fade in, hold for `hold_ms`, then fade out."""
        self._hide_timer.stop()
        if self._anim.state() == QPropertyAnimation.Running:
            self._anim.stop()
            self._anim.disconnect()

        self.label.setText(text)
        self.adjustSize()
        self._position_below_orb()
        self.show()
        self._opacity.setOpacity(1.0)
        self._anim.finished.disconnect()

        # Fade out after hold_ms
        self._hide_timer.start(hold_ms)

    def _fade_out(self):
        self._hide_timer.stop()
        self._anim.finished.disconnect()
        self._anim.setStartValue(self._opacity.opacity())
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    def clear(self):
        """Immediately clear and hide the subtitle."""
        self._hide_timer.stop()
        if self._anim.state() == QPropertyAnimation.Running:
            self._anim.stop()
        self.label.setText("")
        self.hide()

    def _position_below_orb(self):
        # Position below the orb if we have a reference; otherwise center screen.
        orb = getattr(self, "_orb_ref", None)
        if orb is not None:
            screen = QApplication.primaryScreen().availableGeometry()
            x = orb.x() + orb.width() // 2 - self.width() // 2
            y = orb.y() + orb.height() + 12
            if y + self.height() > screen.bottom():
                y = orb.y() - self.height() - 12
            self.move(max(screen.left(), min(x, screen.right() - self.width())),
                      max(screen.top(), y))
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(
                screen.right() - self.width() - 38,
                screen.bottom() - self.height() - 130,
            )

    def bind_orb(self, orb):
        self._orb_ref = orb


class CompanionApp:
    def __init__(self, app: QApplication):
        self.app=app; self.settings=Settings.load(); from ..logging_setup import configure_logging
        self.log=configure_logging(self.settings.log_level); initialize(); self.agent=OllamaAgent(self.settings,self.log); self.tts=SpeechEngine(self.log); self.pool=QThreadPool.globalInstance()
        self.orb=OrbWindow(self.open_chat,self.settings,self); self.chat=ChatWindow(self); self.subtitle=SubtitleWindow(self.settings.glass_panels); self.settings_win=None; self.debug=None
        self.tray=QSystemTrayIcon(self._icon(),app); menu=QMenu(); a=QAction("Open chat",app); a.triggered.connect(self.open_chat); menu.addAction(a)
        b=QAction("Settings",app); b.triggered.connect(self.open_settings); menu.addAction(b)
        c=QAction("Diagnostics",app); c.triggered.connect(self.toggle_debug); menu.addAction(c); menu.addSeparator()
        d=QAction("Quit Crystal",app); d.triggered.connect(app.quit); menu.addAction(d); self.tray.setContextMenu(menu); self.tray.setToolTip("Crystal Companion · local AI"); self.tray.show()
        self.log.info("Crystal Companion started | config=%s", APP_DIR/"settings.json")
        self.orb.show()
    def _icon(self):
        from PySide6.QtGui import QPixmap
        pix=QPixmap(32,32); pix.fill(Qt.transparent); p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing); p.setBrush(QColor(105,210,255,200)); p.setPen(QPen(QColor(220,250,255),2)); p.drawEllipse(3,3,26,26); p.end(); return QIcon(pix)
    def open_chat(self, settings_only=False):
        if settings_only: self.open_settings(); return
        self.chat.place_under_orb(self.orb); self.chat.show(); self.chat.raise_(); self.chat.activateWindow(); self.chat.entry.setFocus()
    def open_settings(self):
        if self.settings_win is None:
            self.settings_win=SettingsWindow(self.settings,self.log); self.settings_win.saved.connect(self.apply_settings); self.settings_win.finished.connect(lambda _: setattr(self,"settings_win",None))
        self.settings_win.show(); self.settings_win.raise_(); self.settings_win.activateWindow()
    def apply_settings(self,s):
        self.settings=s; self.agent.settings=s; self.orb.apply_settings(s); self.chat.set_glass_enabled(s.glass_panels)
        self.subtitle.set_glass_enabled(s.glass_panels)
        if self.settings_win is not None: self.settings_win.set_glass_enabled(s.glass_panels)
        if self.debug is not None: self.debug.set_glass_enabled(s.glass_panels)
        self.log.setLevel(getattr(logging,s.log_level,logging.DEBUG)); self.log.info("Runtime settings applied")

    def _handle_voice_query(self, text: str):
        """Process recognized speech as a user query: show in chat + subtitles, save history, get answer."""
        self.log.info("Voice query received (%d chars)", len(text))
        # Show user's spoken input in the chat transcript
        self.chat.append("YOU", text)
        # Show it in subtitles too
        self.subtitle.bind_orb(self.orb)
        self.subtitle.show_text(text, hold_ms=1500)

        old = recent(self.chat.session_id) if self.settings.remember_history else []
        self.chat.busy = True
        self.chat.send_btn.setEnabled(False)
        self.chat.status.setText("◌ THINKING")
        self.orb.set_state("thinking")

        worker = Worker(lambda: asyncio.run(self.agent.ask(text, old, self.settings)))
        worker.signals.result.connect(lambda answer: self._on_voice_answer(text, answer))
        worker.signals.error.connect(self._on_voice_error_answer)
        self.pool.start(worker)

    def _on_voice_answer(self, query: str, answer: str):
        self.log.info("Voice assistant response received (%d chars)", len(answer))
        self.chat.append("CRYSTAL", answer)
        self.subtitle.bind_orb(self.orb)
        self.subtitle.show_text(answer, hold_ms=3000)
        if self.settings.remember_history:
            add(self.chat.session_id, "user", query)
            add(self.chat.session_id, "assistant", answer)
        self.chat.busy = False
        self.chat.send_btn.setEnabled(True)
        self.chat.status.setText("● READY")
        self.orb.set_state("speaking" if self.settings.tts_enabled else "idle")
        if self.settings.tts_enabled:
            self.chat.status.setText("♫ SPEAKING / LOADING TTS")
            w = Worker(lambda: self.tts.synthesize(answer, self.settings.tts_model, self.settings.tts_speed, self.settings.tts_device))
            w.signals.result.connect(self.chat.play_audio)
            w.signals.error.connect(self.chat.tts_error)
            self.pool.start(w)
        else:
            self.orb.set_state("idle")

    def _on_voice_error_answer(self, message: str):
        self.log.error("Voice request failed: %s", message)
        self.chat.append("ERROR", message)
        self.subtitle.bind_orb(self.orb)
        self.subtitle.show_text(f"Error: {message}", hold_ms=3000)
        self.chat.busy = False
        self.chat.send_btn.setEnabled(True)
        self.chat.status.setText("! ERROR")
        self.orb.set_state("error")

    def toggle_debug(self):
        if self.debug is None: self.debug=DebugWindow(self.settings.glass_panels); self.debug.finished.connect(lambda _: setattr(self,"debug",None))
        self.debug.show(); self.debug.raise_(); self.debug.activateWindow()

STYLE = """
QWidget { color: #e7efff; font-family: 'Segoe UI'; font-size: 10pt; }
QDialog#glass { background: transparent; border: none; }
QWidget#panel { background: transparent; border: none; }
QLabel#title { color: #b8d9ff; font-size: 9pt; font-weight: 700; letter-spacing: 1px; }
QLabel#status { color: #8fffd8; font-size: 8pt; }
QTextEdit#transcript, QTextEdit { background: rgba(5,10,22,175); border: 1px solid rgba(130,160,220,55); border-radius: 10px; padding: 8px; selection-background-color: #405b9c; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: rgba(5,10,24,230); border: 1px solid rgba(130,170,230,95); border-radius: 9px; padding: 9px; selection-background-color: #405b9c; }
QPushButton { background: rgba(65,105,170,100); border: 1px solid rgba(150,195,255,90); border-radius: 9px; padding: 8px 12px; }
QPushButton:hover { background: rgba(75,140,220,150); }
QPushButton:disabled { color: #77839d; }
QTabWidget::pane { border: 1px solid rgba(130,170,230,70); border-radius: 10px; padding: 8px; }
QTabBar::tab { background: rgba(50,70,110,80); padding: 10px 16px; margin: 3px; border-radius: 8px; }
QTabBar::tab:selected { background: rgba(75,130,220,145); }
QListWidget { background: rgba(5,10,24,230); border: 1px solid rgba(130,170,230,80); border-radius: 8px; padding: 6px; }
QCheckBox { spacing: 8px; }
QLabel#subtitle { color: #e7efff; font-size: 11pt; font-weight: 600; background: transparent; }
"""
