from PyQt5.QtWidgets import QStatusBar, QLabel, QLineEdit, QProgressBar
from src.tools.myThread import MyProgressBarThread


class MyStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.scale_info = QLineEdit()
        self.scale_info.setFixedSize(150, 20)
        self.scale_info.setEnabled(False)
        self.scale_tag = QLabel("放大镜：")
        self.addPermanentWidget(self.scale_tag)
        self.addPermanentWidget(self.scale_info)

        self.xy_info = QLineEdit()
        self.xy_info.setFixedSize(150, 20)
        self.xy_info.setEnabled(False)
        self.xy_tag = QLabel("坐标：")
        self.addPermanentWidget(self.xy_tag)
        self.addPermanentWidget(self.xy_info)

        self.geo_info = QLineEdit()
        self.geo_info.setFixedSize(150, 20)
        self.geo_info.setEnabled(False)
        self.geo_tag = QLabel("经纬度：")
        self.addPermanentWidget(self.geo_tag)
        self.addPermanentWidget(self.geo_info)

        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(100)
        self.addWidget(self.progressBar)
        self.progressBar.hide()

        self.scale_tag.setBuddy(self.scale_info)
        self.xy_tag.setBuddy(self.xy_info)
        self.geo_tag.setBuddy(self.geo_info)

    def showLocation(self, meg1, meg2):
        self.xy_info.setText(meg1)
        self.geo_info.setText(meg2)

    def showScale(self, meg):
        self.scale_info.setText(meg)

    def start_progress_bar(self):
        self.progressBar.setValue(0)
        self.progressBar.show()
        self.update_thread = MyProgressBarThread()
        self.update_thread.progress_update.connect(self.updateProgressBar)
        self.update_thread.start()

    def updateProgressBar(self, stepValue):
        self.progressBar.setValue(self.progressBar.value() + stepValue)

    def end_progress_bar(self):
        print("end bar\n")
        self.update_thread.quit()
        self.progressBar.hide()
