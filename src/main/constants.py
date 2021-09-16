picture_descr = {0: 'other',
                 1: '32x32 pixels file icon',
                 2: 'Other file icon',
                 3: 'Cover (front)',
                 4: 'Cover (back)',
                 5: 'Leaflet page',
                 6: 'Media',
                 7: 'Lead artist/lead performer/soloist',
                 8: 'Artist/performer',
                 9: 'Conductor',
                 10: 'Band/Orchestra',
                 11: 'Composer',
                 12: 'Lyricist/text writer',
                 13: 'Recording Location',
                 14: 'During recording',
                 15: 'During performance',
                 16: 'Movie/video screen capture',
                 17: 'A bright coloured fish',
                 18: 'Illustration',
                 19: 'Band/artist logotype',
                 20: 'Publisher/Studio logotype'}

channels = {8: 'left/side stereo', 9: 'right/side stereo',
            10: 'mid/side stereo'}

sample_size = {1: 8, 2: 12, 4: 16, 5: 20, 6: 24}

sample_rate = {1: 88.2, 2: 176.4, 3: 192, 4: 8, 5: 16, 6: 22.05, 7: 24, 8: 32,
               9: 44.1, 10: 48, 11: 96}

text = '''STREAMINFO:
        minimum block size: {0} samples
        maximum block size: {1} samples
        minimum frame size: {2} bytes
        maximum frame size: {3} bytes
        sample rate: {4} Hz
        number of channels: {5}
        bits per sample: {6}
        samples in stream: {7}'''

pic_text = '''{0}. Type of picture:{1}
                Format of picture: {2}
                Description: {3}
                Width: {4}
                Height: {5}
                Color depth: {6}
                Number of colors: {7}\n'''

frames_text = '''frame {0}:
                           offset {1}
                           block size: {2}
                           samples sample rate {3}: kHz
                           channels {4}
                           sample size {5} bits per sample'''

sample_number_text = '\n                           sample number: {}'

cuesheet_text = '''\nCUESHEET:
            Media catalog number: {0}
            Lead-in samples: {1}
            Corresponds to CD: {2}'''
track_text = '{0}. Offset: {1}, ISRC: {2}, Track type: {3}, pre-emphasis: {4}'
