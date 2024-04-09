from qtpy.QtWidgets import QGraphicsOpacityEffect, QFrame, QWidget, QComboBox, QLabel, QSizePolicy, QDialog, QProgressBar, QMessageBox, QVBoxLayout, QStyle, QSlider, QProxyStyle, QStyle, QStyleOptionSlider, QColorDialog, QPushButton
from qtpy.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPointF, QRect, Signal
from qtpy.QtGui import QFontMetrics, QMouseEvent, QShowEvent, QWheelEvent, QPainter, QFontMetrics, QColor
from typing import List, Union, Tuple

from utils.shared import CONFIG_COMBOBOX_LONG, CONFIG_COMBOBOX_MIDEAN, CONFIG_COMBOBOX_SHORT, HORSLIDER_FIXHEIGHT
from utils import shared as C


class Widget(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


class FadeLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # https://stackoverflow.com/questions/57828052/qpropertyanimation-not-working-with-window-opacity
        effect = QGraphicsOpacityEffect(self, opacity=1.0)
        self.setGraphicsEffect(effect)
        self.fadeAnimation = QPropertyAnimation(
            self,
            propertyName=b"opacity",
            targetObject=effect,
            duration=1200,
            startValue=1.0,
            endValue=0.,
        )
        self.fadeAnimation.setEasingCurve(QEasingCurve.InQuint)
        self.fadeAnimation.finished.connect(self.hide)
        self.setHidden(True)
        self.gv = None

    def startFadeAnimation(self):
        self.show()
        self.fadeAnimation.stop()
        self.fadeAnimation.start()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.gv is not None:
            self.gv.wheelEvent(event)
        return super().wheelEvent(event)


class SeparatorWidget(QFrame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class TaskProgressBar(Widget):
    def __init__(self, description: str = '', *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.progressbar = QProgressBar(self)
        self.progressbar.setTextVisible(False)
        self.textlabel = QLabel(self)
        self.description = description
        self.text_len = 100
        layout = QVBoxLayout(self)
        layout.addWidget(self.textlabel)
        layout.addWidget(self.progressbar)
        self.updateProgress(0)

    def updateProgress(self, progress: int, msg: str = ''):
        self.progressbar.setValue(progress)
        if self.description:
            msg = self.description + msg
        if len(msg) > self.text_len - 3:
            msg = msg[:self.text_len - 3] + '...'
        elif len(msg) < self.text_len:
            msg = msg + ' ' * (self.text_len - len(msg))
        self.textlabel.setText(msg)
        self.progressbar.setValue(progress)


class FrameLessMessageBox(QMessageBox):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        

class ProgressMessageBox(QDialog):
    showed = Signal()
    def __init__(self, task_name: str = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(20, 10, 20, 30)

        self.task_progress_bar: TaskProgressBar = None
        if task_name is not None:
            self.task_progress_bar = TaskProgressBar(task_name)
            layout.addWidget(self.task_progress_bar)

    def updateTaskProgress(self, value: int, msg: str = ''):
        if self.task_progress_bar is not None:
            self.task_progress_bar.updateProgress(value, msg)

    def setTaskName(self, task_name: str):
        if self.task_progress_bar is not None:
            self.task_progress_bar.description = task_name

    def showEvent(self, e: QShowEvent) -> None:
        self.showed.emit()
        return super().showEvent(e)


class ImgtransProgressMessageBox(ProgressMessageBox):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(None, *args, **kwargs)
        
        self.detect_bar = TaskProgressBar(self.tr('Detecting: '), self)
        self.ocr_bar = TaskProgressBar(self.tr('OCR: '), self)
        self.inpaint_bar = TaskProgressBar(self.tr('Inpainting: '), self)
        self.translate_bar = TaskProgressBar(self.tr('Translating: '), self)

        layout = self.layout()
        layout.addWidget(self.detect_bar)
        layout.addWidget(self.ocr_bar)
        layout.addWidget(self.inpaint_bar)
        layout.addWidget(self.translate_bar)

    def updateDetectProgress(self, value: int, msg: str = ''):
        self.detect_bar.updateProgress(value, msg)

    def updateOCRProgress(self, value: int, msg: str = ''):
        self.ocr_bar.updateProgress(value, msg)

    def updateInpaintProgress(self, value: int, msg: str = ''):
        self.inpaint_bar.updateProgress(value, msg)

    def updateTranslateProgress(self, value: int, msg: str = ''):
        self.translate_bar.updateProgress(value, msg)
    
    def zero_progress(self):
        self.updateDetectProgress(0)
        self.updateOCRProgress(0)
        self.updateInpaintProgress(0)
        self.updateTranslateProgress(0)

    def show_all_bars(self):
        self.detect_bar.show()
        self.ocr_bar.show()
        self.translate_bar.show()
        self.inpaint_bar.show()

    def hide_all_bars(self):
        self.detect_bar.hide()
        self.ocr_bar.hide()
        self.translate_bar.hide()
        self.inpaint_bar.hide()


class ColorPicker(QLabel):
    colorChanged = Signal(bool)
    changingColor = Signal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color: QColor = None

    def mousePressEvent(self, event):
        self.changingColor.emit()
        color = QColorDialog.getColor()
        is_valid = color.isValid()
        if is_valid:
            self.setPickerColor(color)
        self.colorChanged.emit(is_valid)

    def setPickerColor(self, color: Union[QColor, List, Tuple]):
        if not isinstance(color, QColor):
            color = QColor(*color)
        self.color = color
        r, g, b, a = color.getRgb()
        rgba = f'rgba({r}, {g}, {b}, {a})'
        self.setStyleSheet("background-color: " + rgba)

    def rgb(self) -> List:
        color = self.color
        return (color.red(), color.green(), color.blue())

    def rgba(self) -> List:
        color = self.color
        return (color.red(), color.green(), color.blue(), color.alpha())


class SliderProxyStyle(QProxyStyle):

    def subControlRect(self, cc, opt, sc, widget):
        r = super().subControlRect(cc, opt, sc, widget)
        if widget.orientation() == Qt.Orientation.Horizontal:
            y = widget.height() // 4
            h = y * 2
            r = QRect(r.x(), y, r.width(), h)
        else:
            x = widget.width() // 4
            w = x * 2
            r = QRect(x, r.y(), w, r.height())

        # seems a bit dumb, otherwise the handle is buggy
        if r.height() < r.width():
            r.setHeight(r.width())
        else:
            r.setWidth(r.height())
        return r
    
def slider_subcontrol_rect(r: QRect, widget: QWidget):
    if widget.orientation() == Qt.Orientation.Horizontal:
        y = widget.height() // 4
        h = y * 2
        r = QRect(r.x(), y, r.width(), h)
    else:
        x = widget.width() // 4
        w = x * 2
        r = QRect(x, r.y(), w, r.height())

    # seems a bit dumb, otherwise the handle is buggy
    if r.height() < r.width():
        r.setHeight(r.width())
    else:
        r.setWidth(r.height())
    return r


class PaintQSlider(QSlider):

    # its pretty buggy, got to replace it someday

    mouse_released = Signal()

    def __init__(self, draw_content = None, orientation=Qt.Orientation.Horizontal, *args, **kwargs):
        super(PaintQSlider, self).__init__(orientation, *args, **kwargs)
        self.draw_content = draw_content
        self.pressed: bool = False
        # self.setStyle(SliderProxyStyle(None))
        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(HORSLIDER_FIXHEIGHT)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressed = True
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressed = False
            self.mouse_released.emit()
        return super().mouseReleaseEvent(event)

    def paintEvent(self, _):
        option = QStyleOptionSlider()
        self.initStyleOption(option)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 中间圆圈的位置
        rect = self.style().subControlRect(
            QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self)
        rect = slider_subcontrol_rect(rect, self)
        
        value = self.value()
        
        # 画中间白色线条
        painter.setPen(QColor(85,85,96))
        painter.setBrush(QColor(85,85,96))
        if self.orientation() == Qt.Orientation.Horizontal:
            y = self.height() / 2
            painter.drawLine(QPointF(4, y), QPointF(self.width() - 8, y))
        else:
            x = self.width() / 2
            painter.drawLine(QPointF(x, 0), QPointF(x, self.height()))
        # 画圆
        painter.setPen(Qt.NoPen)

        r = rect.height() // 2
        vr = int((value - self.minimum()) / (self.maximum() - self.minimum()) * r)
        rect = QRect(rect.x() - vr, rect.y(), rect.width(), rect.width())

        if option.state & QStyle.State_MouseOver:  # 双重圆
            
            r = rect.height() / 2
            painter.setBrush(QColor(*C.SLIDERHANDLE_COLOR,100))
            painter.drawRoundedRect(rect, r, r)
            # 实心小圆(上下左右偏移4)
            rect_inner = rect.adjusted(4, 4, -4, -4)
            r = rect_inner.height() // 2
            painter.setBrush(QColor(*C.SLIDERHANDLE_COLOR,255))
            painter.drawRoundedRect(rect_inner, r, r)

            painter.setPen(QColor(*C.SLIDERHANDLE_COLOR,255))
            font = painter.font()
            font.setPointSizeF(8)
            fm = QFontMetrics(font)
            painter.setFont(font)

            is_hor = self.orientation() == Qt.Orientation.Horizontal
            if is_hor:  # 在上方绘制文字
                x, y = rect.x(), rect.y()
                dx, dy = x, y
                if value < (self.maximum() + self.minimum()) / 2:
                    dx += rect.width()
                else:
                    dx -= rect.width()
            else:  # 在左侧绘制文字
                x, y = rect.x() - rect.width(), rect.y()


            painter.drawText(
                dx, self.height() - fm.height(), str(value), 
            )

            if self.draw_content is not None:
                painter.drawText(
                    0, dy, self.draw_content, 
                )

        else:  # 实心圆
            rect = rect.adjusted(4, 4, -4, -4)
            r = rect.height() // 2
            painter.setBrush(QColor(*C.SLIDERHANDLE_COLOR,200))
            painter.drawRoundedRect(rect, r, r)

class CustomComboBox(QComboBox):
    # https://stackoverflow.com/questions/3241830/qt-how-to-disable-mouse-scrolling-of-qcombobox
    def __init__(self, scrollWidget=None, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        self.scrollWidget=scrollWidget
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        if self.scrollWidget is None or self.hasFocus():
            return super().wheelEvent(*args, **kwargs)
        else:
            return self.scrollWidget.wheelEvent(*args, **kwargs)
        

class ConfigComboBox(CustomComboBox):

    def __init__(self, fix_size=True, scrollWidget: QWidget = None, *args, **kwargs) -> None:
        super().__init__(scrollWidget, *args, **kwargs)
        self.fix_size = fix_size
        self.adjustSize()

    def addItems(self, texts: List[str]) -> None:
        super().addItems(texts)
        self.adjustSize()

    def adjustSize(self) -> None:
        super().adjustSize()
        width = self.minimumSizeHint().width()
        if width < CONFIG_COMBOBOX_SHORT:
            width = CONFIG_COMBOBOX_SHORT
        elif width < CONFIG_COMBOBOX_MIDEAN:
            width = CONFIG_COMBOBOX_MIDEAN
        else:
            width = CONFIG_COMBOBOX_LONG
        if self.fix_size:
            self.setFixedWidth(width)
        else:
            self.setMaximumWidth(width)


class ClickableLabel(QLabel):

    clicked = Signal()

    def __init__(self, text=None, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        if text is not None:
            self.setText(text)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return super().mousePressEvent(e)
    
class IgnoreMouseLabel(QLabel):

    def mousePressEvent(self, e: QMouseEvent) -> None:
        e.ignore()
        return super().mousePressEvent(e)
    
class CheckableLabel(QLabel):

    checkStateChanged = Signal(bool)

    def __init__(self, checked_text: str, unchecked_text: str, default_checked: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checked_text = checked_text
        self.unchecked_text = unchecked_text
        self.checked = default_checked
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if default_checked:
            self.setText(checked_text)
        else:
            self.setText(unchecked_text)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self.checked)
            self.checkStateChanged.emit(self.checked)
        return super().mousePressEvent(e)

    def setChecked(self, checked: bool):
        self.checked = checked
        if checked:
            self.setText(self.checked_text)
        else:
            self.setText(self.unchecked_text)


class NoBorderPushBtn(QPushButton):
    pass

class TextChecker(QLabel):
    checkStateChanged = Signal(bool)
    def __init__(self, text: str, checked: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setText(text)
        self.setCheckState(checked)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setCheckState(self, checked: bool):
        self.checked = checked
        if checked:
            self.setStyleSheet("QLabel { background-color: rgb(30, 147, 229); color: white; }")
        else:
            self.setStyleSheet("")

    def isChecked(self):
        return self.checked

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCheckState(not self.checked)
            self.checkStateChanged.emit(self.checked)


