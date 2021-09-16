import re
import pathlib
import sys

# TODO переделать
sys.path.append(str(pathlib.Path(__file__).parent))

import constants
from CRC8 import CRC8

crc8 = CRC8()
ext_regex = re.compile('.+?/(.+)')


class AudioFile:
    def __init__(self, filename):
        self.filename = filename
        self.file_is_flac()
        self.frames = []
        self.positions = {}
        self.first_frame = self.parse_metadata()
        self.streaminfo = {}
        self.parse_streaminfo()
        self.blocking_strategy = self.__get_blocking_strategy()
        self.tags = None
        self.picture = []
        self.cuesheet = {}
        self.seektable = []
        if 'vorbis comment' in self.positions:
            self.tags = self.parse_vorbis_comment()
        if 'picture' in self.positions:
            for i in range(0, len(self.positions['picture'])):
                self.picture.append(self.parse_picture(i))
        if 'cuesheet' in self.positions:
            self.cuesheet = self.parse_cuesheet()
        if 'seektable' in self.positions:
            self.seektable = self.parse_seektable()

    def file_is_flac(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            if file[0:4].decode() != 'fLaC':
                raise ValueError('file is not flac')

    @staticmethod
    def parse_metadata_block_header(header):
        flag_and_type = bin(header[0])[2:].zfill(8)
        is_last = int(flag_and_type[0])
        type_of_block = int(flag_and_type[1:], 2)
        size = int.from_bytes(header[1:], byteorder='big')
        return is_last, type_of_block, size

    def parse_vorbis_comment(self):
        tags = {}
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions['vorbis comment']
            block = file[begin:end]
        vendor_length = int.from_bytes(block[0:4], byteorder='little')
        vendor = block[4:4+vendor_length].decode()
        tags['vendor'] = vendor
        tags_count = int.from_bytes(block[4+vendor_length:8+vendor_length],
                                    byteorder='little')
        pos = 8 + vendor_length
        tag_regex = re.compile('(.+?)=(.+)')
        for i in range(0, tags_count):
            length = int.from_bytes(block[pos:pos+4], byteorder='little')
            tag = tag_regex.match(block[pos+4:pos+4+length].decode())
            if tag:
                tag_name = tag.group(1)
                tag_value = tag.group(2)
                if tag_name in tags:
                    tags[tag_name].add(tag_value)
                else:
                    tags[tag_name] = {tag_value}
            pos += 4 + length
        return tags

    def parse_streaminfo(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions['streaminfo']
            block = file[begin:end]
        self.streaminfo['block_minsize'] = \
            int.from_bytes(block[0:2], byteorder='big')
        self.streaminfo['block_maxsize'] = \
            int.from_bytes(block[2:4], byteorder='big')
        self.streaminfo['frame_minsize'] = \
            int.from_bytes(block[4:7], byteorder='big')
        self.streaminfo['frame_maxsize'] = \
            int.from_bytes(block[7:10], byteorder='big')
        data = bin(int.from_bytes(block[10:18], byteorder='big'))[2:].zfill(64)
        self.streaminfo['rate'] = int(data[0:20], 2)
        self.streaminfo['channels'] = int(data[20:23], 2) + 1
        self.streaminfo['bits per sample'] = int(data[23:28], 2) + 1
        self.streaminfo['samples in flow'] = int(data[28:64], 2)

    def parse_picture(self, i):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions['picture'][i]
            block = file[begin:end]

        ext_len = int.from_bytes(block[4:8], byteorder='big')
        descr_len = int.from_bytes(block[8 + ext_len:12 + ext_len],
                                   byteorder='big')
        pic_len = int.from_bytes(block[28 + ext_len + descr_len:
                                       32 + ext_len + descr_len],
                                 byteorder='big')

        pic_type = self.__get_pic_type(block)
        mime_type = self.__get_mime_type(block, ext_len)
        ext = ext_regex.match(mime_type).group(1)
        descr = self.__get_description(block, ext_len, descr_len)
        width, height = self.__get_sizes(block, ext_len, descr_len)
        color_depth, number_of_colors = \
            self.__get_colors(block, ext_len, descr_len)
        pic = self.__get_picture(block, ext_len, descr_len, pic_len)
        return {'picture type': pic_type,
                'mime type': mime_type,
                'extension': ext,
                'description': descr,
                'width': width,
                'height': height,
                'color depth': color_depth,
                'number of colors': number_of_colors,
                'pic': pic}

    @staticmethod
    def __get_pic_type(block):
        return constants.picture_descr[int.from_bytes(block[0:4],
                                                      byteorder='big')]

    @staticmethod
    def __get_mime_type(block, ext_len):
        return block[8:8+ext_len].decode()

    @staticmethod
    def __get_description(block, ext_len, descr_len):
        return block[12 + ext_len:12 + ext_len + descr_len].decode()

    @staticmethod
    def __get_sizes(block, ext_len, descr_len):
        width = int.from_bytes(block[12 + ext_len + descr_len:
                                     16 + ext_len + descr_len],
                               byteorder='big')
        height = int.from_bytes(block[16 + ext_len + descr_len:
                                      20 + ext_len + descr_len],
                                byteorder='big')
        return width, height

    @staticmethod
    def __get_colors(block, ext_len, descr_len):
        color_depth = int.from_bytes(block[20 + ext_len + descr_len:
                                           24 + ext_len + descr_len],
                                     byteorder='big')
        number_of_colors = int.from_bytes(block[24 + ext_len + descr_len:
                                                28 + ext_len + descr_len],
                                          byteorder='big')
        return color_depth, number_of_colors

    @staticmethod
    def __get_picture(block, ext_len, descr_len, pic_len):
        return block[32+ext_len+descr_len:32+ext_len+descr_len+pic_len]

    def parse_metadata(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            pos = 4
            is_last = False
            while not is_last:
                is_last, type_of_block, size = \
                    self.parse_metadata_block_header(file[pos:pos+4])
                positions = (pos+4, pos+4+size)
                if type_of_block == 0:
                    self.positions['streaminfo'] = positions
                if type_of_block == 4:
                    self.positions['vorbis comment'] = positions
                if type_of_block == 6:
                    if 'picture' not in self.positions:
                        self.positions['picture'] = [positions]
                    else:
                        self.positions['picture'].append(positions)
                if type_of_block == 5:
                    self.positions['cuesheet'] = positions
                pos += size + 4
                if type_of_block == 3:
                    self.positions['seektable'] = positions
        return pos

    def parse_cuesheet(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions['cuesheet']
            block = file[begin:end]
        cuesheet = {}
        cuesheet['media catalog number'] = block[0:128].decode()
        cuesheet['lead in samples'] = int.from_bytes(block[128:136],
                                                     byteorder='big')
        cuesheet['corresponds to cd'] = int(bin(block[136])[2])
        number_of_tracks = block[395]
        cuesheet['tracks'] = []
        pos = 396
        for i in range(0, number_of_tracks):
            cuesheet['tracks'].append({})
            cuesheet['tracks'][i]['offset'] = int.from_bytes(block[pos:pos+8],
                                                             byteorder='big')
            cuesheet['tracks'][i]['track number'] = block[pos+8]
            cuesheet['tracks'][i]['isrc'] = block[pos+9:pos+21].decode()
            cuesheet['tracks'][i]['is audio'] = int(bin(block[pos+21])
                                                    .zfill(8)[2])
            cuesheet['tracks'][i]['pre-emphasis'] = int(bin(block[pos+21])
                                                        .zfill(8)[3])
            number_of_track_points = block[pos+35]
            pos += 36
            cuesheet['tracks'][i]['track index'] = []
            for j in range(0, number_of_track_points):
                cuesheet['tracks'][i]['track index'].append({})
                cuesheet['tracks'][i]['track index'][j]['offset'] = \
                    int.from_bytes(block[pos:pos+8], byteorder='big')
                cuesheet['tracks'][i]['track index'][j]['index point number'] \
                    = block[pos+8]
                pos += 12
        return cuesheet

    def parse_seektable(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions['seektable']
            block = file[begin:end]
        pos = 0
        seektable = []
        counter = 0
        while pos + 17 < len(block):
            seektable.append({})
            seektable[counter]['first sample'] = block[pos:pos+8]
            seektable[counter]['offset'] = block[pos+8:pos+16]
            seektable[counter]['number of samples'] = block[pos+16:pos+18]
            pos += 18
            counter += 1
        return seektable

    def __get_blocking_strategy(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
        return bin(file[self.first_frame + 1])[-1]

    def parse_frames(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            pos = self.first_frame
            counter = -1
            while pos < len(file):
                if not (b'\xff\xfb' >= file[pos:pos+2] >= b'\xff\xf8'):
                    pos += 1
                else:
                    counter += 1
                    try:
                        block_size, sample_rate, channels, sample_size, \
                         offset, \
                         frame_sample_number = \
                         self.parse_one_frame(file, pos, counter)
                    except ValueError:
                        counter -= 1
                        pos += 1
                        continue
                    self.frames.append({})
                    self.frames[counter]['block size'] = block_size
                    self.frames[counter]['sample rate'] = sample_rate
                    self.frames[counter]['channels'] = channels
                    self.frames[counter]['sample size'] = sample_size
                    self.frames[counter]['offset'] = pos
                    pos = offset
                    if self.blocking_strategy:
                        self.frames[counter]['sample number'] = \
                            frame_sample_number

    @staticmethod
    def __decode_utf8(file, pos):
        number_of_bytes = 1
        first_byte = bin(file[pos])[2:].zfill(8)
        while first_byte[number_of_bytes - 1] == '1':
            number_of_bytes += 1
            if number_of_bytes == 8:
                raise ValueError()
        if number_of_bytes == 1:
            number = first_byte[1:]
        else:
            number_of_bytes -= 1
            number = first_byte[number_of_bytes + 1:]
        for i in range(pos + 1, pos + number_of_bytes):
            number += bin(file[i])[4:]
        return number_of_bytes, int(number, 2)

    def __get_block_size(self, file, pos, length, block_size):
        block_size_len = 0
        if block_size == 0:
            block_size = self.streaminfo['block_maxsize']
        if block_size == 1:
            block_size = 192
        if 2 <= block_size <= 5:
            block_size = 576 * 2 ** (block_size - 2)
        if 8 <= block_size <= 15:
            block_size = 256 * 2 ** (block_size - 8)
        if block_size == 6:
            block_size = file[pos + 4 + length] + 1
            block_size_len = 1
        if block_size == 7:
            block_size = int.from_bytes(file[pos + 4 + length:
                                             pos + 6 + length],
                                        byteorder='big') + 1
            block_size_len = 2
        return block_size, block_size_len

    def __get_sample_rate(self, file, pos, length, block_size_len,
                          sample_rate):
        sample_rate_len = 0
        if sample_rate == 15:
            raise ValueError()
        if sample_rate == 0:
            sample_rate = self.streaminfo['rate']
        if 1 <= sample_rate <= 11:
            sample_rate = constants.sample_rate[sample_rate]
        if sample_rate == 12:
            sample_rate = file[pos + 4 + length + block_size_len]
            sample_rate_len = 1
        if sample_rate == 13:
            sample_rate = int.from_bytes(file[pos+4+length+block_size_len:
                                              pos+6+length+block_size_len],
                                         byteorder='big') / 1000
            sample_rate_len = 2
        if sample_rate == 14:
            sample_rate = int.from_bytes(file[pos+4+length+block_size_len:
                                              pos+6+length+block_size_len],
                                         byteorder='big') / 100
            sample_rate_len = 2
        return sample_rate, sample_rate_len

    def parse_one_frame(self, file, pos, counter):
        if bin(file[pos + 1])[-1] != self.blocking_strategy:
            raise ValueError()
        length, frame_sample_number = self.__decode_utf8(file, pos + 4)
        data = bin(file[pos + 2])[2:].zfill(8)
        block_size = int(data[:4], 2)
        block_size, block_size_len = self.__get_block_size(file, pos, length,
                                                           block_size)

        sample_rate = int(data[4:], 2)

        sample_rate, sample_rate_len = self.__get_sample_rate(file, pos,
                                                              length,
                                                              block_size_len,
                                                              sample_rate)

        data = bin(file[pos + 3])[2:].zfill(8)
        channels = int(data[:4], 2)

        if channels >= 11:
            raise ValueError()
        if 0 <= channels <= 7:
            channels += 1
        else:
            channels = constants.channels[channels]

        sample_size = int(data[4:7], 2)

        if sample_size == 3 or sample_size == 7:
            raise ValueError()
        if sample_size == 0:
            sample_size = self.streaminfo['bits per sample']
        else:
            sample_size = constants.sample_size[sample_size]

        if self.blocking_strategy == 0:
            if frame_sample_number != counter:
                raise ValueError()

        end_pos = pos + 4 + block_size_len + sample_rate_len + length
        if file[end_pos] != crc8.get_crc(file[pos:end_pos]):
            raise ValueError()
        pos += 5 + block_size_len + sample_rate_len + length
        return block_size, sample_rate, channels, sample_size, pos, \
            frame_sample_number

    def save_picture(self):
        with open('{0}pic.{1}'.
                  format(self.filename.split('.')[0],
                         self.picture[0]['extension']), 'wb') as f:
            f.write(self.picture[0]['pic'])

    def make_text(self):
        text = constants.text.format(self.streaminfo['block_minsize'],
                                     self.streaminfo['block_maxsize'],
                                     self.streaminfo['frame_minsize'],
                                     self.streaminfo['frame_maxsize'],
                                     self.streaminfo['rate'],
                                     self.streaminfo['channels'],
                                     self.streaminfo['bits per sample'],
                                     self.streaminfo['samples in flow'])
        if self.tags:
            tags = '\nVORBIS COMMENT:'
            for tag in self.tags:
                if tag == 'vendor':
                    continue
                i = 0
                tags += '\n                      {0}: '.format(tag)
                for tag_value in self.tags[tag]:
                    tags += tag_value
                    if i != len(self.tags[tag]) - 1:
                        tags += ', '
                    i += 1
            text += tags

        if len(self.picture) > 0:
            pictures = '\nPICTURES:'
            for i in range(0, len(self.picture)):
                pictures += constants.pic_text.\
                    format(str(i+1),
                           self.picture[i]['picture type'],
                           self.picture[i]['mime type'],
                           self.picture[i]['description'],
                           self.picture[i]['width'],
                           self.picture[i]['height'],
                           self.picture[i]['color depth'],
                           self.picture[i]['number of colors'])
            text += pictures

        if len(self.cuesheet) > 0:
            cuesheet_text = \
                constants.cuesheet_text.format(self.cuesheet
                                               ['media catalog number'],
                                               self.cuesheet
                                               ['lead in samples'],
                                               self.cuesheet
                                               ['corresponds to cd'])
            for i in range(0, len(self.cuesheet['tracks'])):
                track_text = constants.track_text.\
                    format(self.cuesheet['tracks'][i]['track number'],
                           self.cuesheet['tracks'][i]['offset'],
                           self.cuesheet['tracks'][i]['isrc'],
                           self.cuesheet['tracks'][i]['is audio'],
                           self.cuesheet['tracks'][i]['pre-emphasis'])
                for j in range(0, len(self.cuesheet['tracks']
                                      [i]['track index'])):
                    track_index_text = '\n{0}. Offset {1}'\
                        .format(self.cuesheet['tracks'][i]['track index'][j]
                                             ['index point number'],
                                self.cuesheet['tracks'][i]['track index'][j]
                                             ['offset'])
                    track_text += track_index_text
                cuesheet_text += track_text
            text += cuesheet_text
        return text

    def save_frames_text(self):
        text = ''
        for i in range(0, len(self.frames)):
            text += constants.frames_text.format(i,
                                                 self.frames[i]['offset'],
                                                 self.frames[i]['block size'],
                                                 self.frames[i]['sample rate'],
                                                 self.frames[i]['channels'],
                                                 self.frames[i]['sample size'])
            if self.blocking_strategy:
                text += \
                    constants.sample_number_text.format(self.frames[i]
                                                        ['sample number'])
            text += '\n\n'
        with open(self.filename.split('.')[0] + ' frames.txt', 'w') as f:
            f.write(text)
