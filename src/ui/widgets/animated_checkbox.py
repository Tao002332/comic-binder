from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPointF, QRectF, Property, QSize
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import QPainter, QPen, QBrush, QLinearGradient, QColor, QPainterPath
from PySide6.QtWidgets import QCheckBox, QStyle, QStyleOptionButton


class AnimatedCheckBox(QCheckBox):
    """Custom checkbox: 135deg gradient fill, glow, bounce pulse, checkmark draw animation."""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.__pulse = 0.0
        self.__check_draw = 0.0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Pulse animation: scale bounce
        self._pulse_anim = QPropertyAnimation(self, b"pulse")
        self._pulse_anim.setDuration(380)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setKeyValueAt(0.30, -1.0)
        self._pulse_anim.setKeyValueAt(0.62, 0.55)
        self._pulse_anim.setEndValue(0.0)

        # Checkmark draw animation: delayed start, longer duration
        self._check_anim = QPropertyAnimation(self, b"checkDraw")
        self._check_anim.setDuration(350)
        self._check_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._check_anim.setStartValue(0.0)
        self._check_anim.setEndValue(1.0)

        self.toggled.connect(self._on_anim_toggle)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self._pressed = False

    # --- Properties for animation ---
    def _get_pulse(self): return self.__pulse
    def _set_pulse(self, v): self.__pulse = v; self.update()
    pulse = Property(float, _get_pulse, _set_pulse)

    def _get_checkDraw(self): return self.__check_draw
    def _set_checkDraw(self, v): self.__check_draw = v; self.update()
    checkDraw = Property(float, _get_checkDraw, _set_checkDraw)

    def _on_anim_toggle(self, checked):
        if checked:
            self.__check_draw = 0.0
            self._pulse_anim.stop()
            self._check_anim.stop()
            self._pulse_anim.start()
            # Delay checkmark draw by 80ms
            from PySide6.QtCore import QTimer
            QTimer.singleShot(80, self._check_anim.start)

    def enterEvent(self, event):
        self._hovered = True; self.update(); super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False; self.update(); super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True; self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False; self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        opt = QStyleOptionButton()
        self.initStyleOption(opt)

        indicator_rect = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, opt, self)
        r = QRectF(indicator_rect)
        r.moveTop((self.height() - 22) / 2.0)
        r.setWidth(22); r.setHeight(22)

        # Scale from pulse animation
        pulse = self.__pulse
        if pulse < 0:
            scale = 1.0 + pulse * 0.18
        elif pulse > 0:
            scale = 1.0 + pulse * 0.10
        else:
            scale = 1.0

        # Pressed shrink
        if self._pressed and not self.isChecked():
            scale *= 0.94

        cx, cy = r.center().x(), r.center().y()
        sr = QRectF(cx - 11 * scale, cy - 11 * scale, 22 * scale, 22 * scale)

        if self.isChecked():
            # Glow
            glow1 = QColor(168, 85, 247, 35)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(glow1)
            p.drawRoundedRect(sr.adjusted(-3, -3, 3, 3), 9, 9)

            glow2 = QColor(99, 102, 241, 15)
            p.setBrush(glow2)
            p.drawRoundedRect(sr.adjusted(-6, -6, 6, 6), 12, 12)

            # 135deg gradient
            grad = QLinearGradient(sr.topLeft(), sr.bottomRight())
            grad.setColorAt(0.0, QColor("#6366f1"))
            grad.setColorAt(0.45, QColor("#a855f7"))
            grad.setColorAt(1.0, QColor("#ec4899"))
            p.setPen(QPen(QColor(99, 102, 241, 80), 1.5))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(sr, 6, 6)

            # Checkmark with draw animation
            draw_progress = self.__check_draw
            if draw_progress < 1.0:
                # Clip region to animate checkmark appearance
                clip_path = QPainterPath()
                clip_rect = QRectF(sr.left() - 2, sr.top() - 2, sr.width() * draw_progress + 4, sr.height() + 4)
                clip_path.addRect(clip_rect)
                p.save()
                p.setClipPath(clip_path)

            check_alpha = min(1.0, draw_progress * 3.0)
            cm = QPainterPath()
            cm.moveTo(sr.left() + 5.5, sr.top() + 11.5)
            cm.lineTo(sr.left() + 9, sr.top() + 15)
            cm.lineTo(sr.left() + 16.5, sr.top() + 7.5)
            check_color = QColor(255, 255, 255, int(255 * check_alpha))
            p.setPen(QPen(check_color, 2.5, Qt.PenStyle.SolidLine,
                         Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(cm)

            if draw_progress < 1.0:
                p.restore()
        else:
            # Unchecked
            if self._hovered:
                border = QColor(168, 85, 247, 102)
                # Hover glow
                hover_glow = QColor(168, 85, 247, 8)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(hover_glow)
                p.drawRoundedRect(sr.adjusted(-5, -5, 5, 5), 10, 10)
            else:
                border = QColor(200, 200, 210, 90)
            p.setPen(QPen(border, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(sr, 6, 6)

        # Draw text if any
        if self.text():
            text_rect = QRectF(r.right() + 8, 0, self.width() - r.right() - 8, self.height())
            p.setPen(QColor("#3c3c43"))
            font = self.font()
            font.setPixelSize(14)
            p.setFont(font)
            p.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())

        p.end()

    def sizeHint(self):
        if self.text():
            fm = self.fontMetrics()
            text_w = fm.horizontalAdvance(self.text())
            return QSize(22 + 8 + text_w + 4, max(fm.height() + 4, 28))
        return QSize(26, 28)

    def hitButton(self, pos):
        r = QRectF(0, (self.height() - 22) / 2.0, 22, 22)
        return r.contains(QPointF(pos))
