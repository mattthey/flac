#!/usr/bin/env python

import sys
from PyQt5.QtCore import QDir, Qt, QUrl, QByteArray
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QPushButton, QSizePolicy, QSlider, QStyle,
                             QVBoxLayout, QWidget)
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction
from PyQt5.QtGui import QIcon, QPixmap, QGuiApplication
from flac import AudioFile


class AudioWindow(QMainWindow):

    def __init__(self, parent=None):
        super(AudioWindow, self).__init__(parent)
        self.setWindowTitle("Flac player")

        self.mediaPlayer = QMediaPlayer()
        self.file_info = None

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.volumeSlider = QSlider(Qt.Vertical)
        self.volumeSlider.setRange(0, 0)
        self.volumeSlider.setValue(100)
        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)
        self.volumeSlider.sliderMoved.connect(self.setVolume)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Maximum)

        self.info_window = InfoWindow(self.file_info)

        # Create new action
        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open flac file')
        openAction.triggered.connect(self.openFile)

        # Create exit action
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitCall)

        self.infoAction = QAction('&File info', self)
        self.infoAction.setStatusTip('Show file info')
        self.infoAction.triggered.connect(self.showInfo)
        self.infoAction.setEnabled(False)

        # Create menu bar and add action
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.infoAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.volumeSlider)

        layout = QVBoxLayout()
        layout.addLayout(controlLayout)
        layout.addWidget(self.errorLabel)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.volumeChanged.connect(self.volumeChanged)
        self.mediaPlayer.error.connect(self.handleError)

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open flac file",
                                                  QDir.homePath())
        if fileName != '':
            try:
                    self.file_info = AudioFile(fileName)

            except ValueError:
                self.infoAction.setEnabled(False)
                self.errorLabel.setText('Error: file is not flac')
                self.mediaPlayer.setMedia(QMediaContent())
                self.playButton.setEnabled(False)
                self.volumeSlider.setRange(0, 0)
            else:
                self.infoAction.setEnabled(True)
                self.volumeSlider.setRange(0, 100)
                self.volumeSlider.setValue(100)
                self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))
                self.errorLabel.setText('')
                self.playButton.setEnabled(True)

    def exitCall(self):
        sys.exit(app.exec_())

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def volumeChanged(self, volume):
        self.volumeSlider.setValue(volume)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def setVolume(self, volume):
        self.mediaPlayer.setVolume(volume)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())

    def showInfo(self):
        self.info_window = InfoWindow(self.file_info)
        self.info_window.show()


class InfoWindow(QWidget):
    def __init__(self, file_info):
        super().__init__()
        self.file_info = file_info
        self.setWindowTitle('Audio info')
        layout = QVBoxLayout(self)
        infoLabel = QLabel()
        infoLabel.setText(self.make_text())
        self.saveButton = QPushButton('Save image')
        self.saveFramesButton = QPushButton('Save frames info')
        if self.file_info:
            self.saveFramesButton.setEnabled(True)
            self.saveFramesButton.clicked.connect(self.save_frames_info)
            if self.file_info.picture:
                self.saveButton.setEnabled(True)
                self.saveButton.clicked.connect(self.file_info.save_picture)
        layout.addWidget(infoLabel)
        layout.addWidget(self.saveButton)
        layout.addWidget(self.saveFramesButton)
        self.setLayout(layout)

    def make_text(self):
        if self.file_info:
            text = self.file_info.make_text()
        else:
            text = ''
        return text

    def save_frames_info(self):
        self.file_info.parse_frames()
        self.file_info.save_frames_text()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = AudioWindow()
    player.resize(640, 200)
    player.show()
    sys.exit(app.exec_())
