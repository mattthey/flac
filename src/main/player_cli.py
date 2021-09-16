import re
import sys
from argparse import ArgumentParser

from PyQt5.QtCore import QUrl, QCoreApplication
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from flac import AudioFile

volume_regex = re.compile(r'v (\d+)')
position_regex = re.compile(r'p ([-+])(\d+)')


class Player:
    def __init__(self):
        self.parser = \
            ArgumentParser(description='flac player',
                           usage="""python player_cli.py -f [filename]
        use flag -p --picture to save picture from file to current directory
        use flag -fr --frames to save frames info
        use commands pl an pa during playing for play and pause
        use command v [int] to set volume
        use command p [int] for rewinding""")
        self.parser.add_argument('-f', '--filename', dest='filename',
                                 action='store', required=True,
                                 help='Input path to the flac file',
                                 metavar='FILE')
        self.parser.add_argument('-p', '--picture', help="Save picture",
                                 action='store_true', required=False)
        self.parser.add_argument('-fr', '--frames', help="Save frames info",
                                 action='store_true', required=False)
        self.args = self.parser.parse_args()
        self.file = AudioFile(self.args.filename)
        if self.args.picture:
            self.file.save_picture()
        self.player = QMediaPlayer()
        self.position = 0
        self.player.\
            setMedia(QMediaContent(QUrl.fromLocalFile(self.file.filename)))
        print(self.file.make_text())
        if self.args.frames:
            self.file.parse_frames()
            self.file.save_frames_text()

        self.player.play()
        self.player.stateChanged.connect(self.mediaStateChanged)

        self.play()

    def play(self):
        while True:
            line = input()
            volume = volume_regex.match(line)
            position = position_regex.match(line)
            self.position = self.player.position()
            if line == 'pa':
                self.player.pause()
            if line == 'pl':
                self.player.play()
            if line == 'stop':
                self.player.stop()
            if volume:
                self.player.setVolume(int(volume.group(1)))
            if position:
                if position.group(1) == '+':
                    pos = int(position.group(2))
                else:
                    pos = -1*int(position.group(2))
                self.position = self.position + pos*100
                self.player.setPosition(self.position)

    def mediaStateChanged(self):
        if self.player.state() == QMediaPlayer.StoppedState:
            sys.exit()


def main():
    app = QCoreApplication(sys.argv)
    player = Player()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
