import unittest
# from flac import AudioFile
from src.main.python.flac import AudioFile

class TestFlacParser(unittest.TestCase):

    def setUp(self):
        self.filename = '../resources/Sample.flac'
        self.filename_with_cuesheet = 'cuesheet_track.flac'
        self.number_of_frames = 3324
        self.audio_file = AudioFile(self.filename)

    def test_assert_file_is_flac(self):
        with self.assertRaises(ValueError):
            AudioFile('not flac.txt')

    def test_assert_instantiates(self):
        self.assertIsNotNone(self.audio_file)

    def test_assert_parsing_is_correct(self):
        self.assertEqual(len(self.audio_file.streaminfo), 8)

    def test_assert_frames_count(self):
        self.audio_file.parse_frames()
        self.assertEqual(len(self.audio_file.frames), self.number_of_frames)

    def test_text_making(self):
        self.assertGreater(len(self.audio_file.make_text()), 0)

    def test_seektable(self):
        self.assertEqual(len(self.audio_file.seektable), 100)

    def test_cuesheet(self):
        file = AudioFile(self.filename_with_cuesheet)
        self.assertGreater(len(file.cuesheet), 0)
