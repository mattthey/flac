import re
import constants
from CRC8 import CRC8
from typing import Final

crc8: Final = CRC8()
ext_regex: Final = re.compile('.+?/(.+)')
tag_regex: Final = re.compile('(.+?)=(.+)')

# streaminfo
STREAMINFO = 'streaminfo'
BLOCK_MINSIZE: Final = 'block_minsize'
BLOCK_MAXSIZE: Final = 'block_maxsize'
VORBIS_COMMENT: Final = 'vorbis comment'
PICTURE: Final = 'picture'
CUESHEET: Final = 'cuesheet'
SEEKTABLE: Final = 'seektable'

RATE = 'rate'
FRAME_MINSIZE = 'frame_minsize'
FRAME_MAXSIZE = 'frame_maxsize'
CHANNELS = 'channels'
BITS_PER_SAMPLE = 'bits per sample'
SAMPLES_IN_FLOW = 'samples in flow'

# cuesheet
MEDIA_CATALOG_NUMBER = 'media catalog number'
LEAD_IN_SAMPLES = 'lead in samples'
CORRESPONDS_TO_CD = 'corresponds to cd'
TRACKS = 'tracks'
OFFSET = 'offset'
TRACK_NUMBER = 'track number'
ISRC = 'isrc'
IS_AUDIO = 'is audio'
PRE_EMPHASIS = 'pre-emphasis'
TRACK_INDEX = 'track index'
INDEX_POINT_NUMBER = 'index point number'

# frames
BLOCK_SIZE = 'block size'
SAMPLE_RATE = 'sample rate'
SAMPLE_SIZE = 'sample size'
SAMPLE_NUMBER = 'sample number'


class AudioFile:
    """
    Разбор метаданных файла flac
    https://xiph.org/flac/format.html
    https://www.the-roberts-family.net/metadata/flac.html
    """
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
        if VORBIS_COMMENT in self.positions:
            self.tags = self.parse_vorbis_comment()
        if PICTURE in self.positions:
            for i in range(0, len(self.positions[PICTURE])):
                self.picture.append(self.parse_picture(i))
        if CUESHEET in self.positions:
            self.cuesheet = self.parse_cuesheet()
        if SEEKTABLE in self.positions:
            self.seektable = self.parse_seektable()

    """
    Проверка на то является ли файл формата flac
    """

    def file_is_flac(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            if file[0:4].decode() != 'fLaC':
                raise ValueError('file is not flac')

    @staticmethod
    def parse_metadata_block_header(header):
        flag_and_type = bin(header[0])[2:].zfill(8)  # заполняем строку 8 нулями
        is_last = int(flag_and_type[0])
        type_of_block = int(flag_and_type[1:], 2)
        size = int.from_bytes(header[1:], byteorder='big')
        return is_last, type_of_block, size

    def parse_vorbis_comment(self):
        """
        Также известное как теги FLAC, содержимое пакета комментариев vorbis, как указано здесь
        (без бита кадрирования). Обратите внимание, что спецификация комментариев vorbis
        допускает порядка 2^64 байтов данных, тогда как блок метаданных FLAC ограничен 2^24 байтами.
        Учитывая заявленную цель комментариев vorbis, т.e. Удобочитаемую текстовую информацию,
        этот предел вряд ли будет ограничивающим. Также обратите внимание, что длины 32-битных полей
        кодируются с прямым порядком байтов в соответствии со спецификацией vorbis, в отличие от обычного
        кодирования с прямым порядком байтов целых чисел фиксированной длины в остальной части FLAC.
        :return:
        """
        tags = {}
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions[VORBIS_COMMENT]
            block = file[begin:end]
        vendor_length = int.from_bytes(block[0:4], byteorder='little')
        vendor = block[4:4 + vendor_length].decode()
        tags['vendor'] = vendor
        tags_count = int.from_bytes(block[4 + vendor_length:8 + vendor_length],
                                    byteorder='little')
        pos = 8 + vendor_length
        for i in range(0, tags_count):
            length = int.from_bytes(block[pos:pos + 4], byteorder='little')
            tag = tag_regex.match(block[pos + 4:pos + 4 + length].decode())
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
            begin, end = self.positions[STREAMINFO]
            block = file[begin:end]
        self.streaminfo[BLOCK_MINSIZE] = int.from_bytes(block[0:2], byteorder='big')
        self.streaminfo[BLOCK_MAXSIZE] = int.from_bytes(block[2:4], byteorder='big')
        self.streaminfo[FRAME_MINSIZE] = int.from_bytes(block[4:7], byteorder='big')
        self.streaminfo[FRAME_MAXSIZE] = int.from_bytes(block[7:10], byteorder='big')
        data = bin(int.from_bytes(block[10:18], byteorder='big'))[2:].zfill(64)
        self.streaminfo[RATE] = int(data[0:20], 2)
        self.streaminfo[CHANNELS] = int(data[20:23], 2) + 1
        self.streaminfo[BITS_PER_SAMPLE] = int(data[23:28], 2) + 1
        self.streaminfo[SAMPLES_IN_FLOW] = int(data[28:64], 2)

    def parse_picture(self, i):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions[PICTURE][i]
            block = file[begin:end]

        ext_len = int.from_bytes(block[4:8], byteorder='big')
        descr_len = int.from_bytes(block[8 + ext_len:12 + ext_len], byteorder='big')
        pic_len = int.from_bytes(block[28 + ext_len + descr_len: 32 + ext_len + descr_len], byteorder='big')

        pic_type = self.__get_pic_type(block)
        mime_type = self.__get_mime_type(block, ext_len)
        ext = ext_regex.match(mime_type).group(1)
        descr = self.__get_description(block, ext_len, descr_len)
        width, height = self.__get_sizes(block, ext_len, descr_len)
        color_depth, number_of_colors = self.__get_colors(block, ext_len, descr_len)
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
        return block[8:8 + ext_len].decode()

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
        return block[32 + ext_len + descr_len:32 + ext_len + descr_len + pic_len]

    def parse_metadata(self):
        """
        Парсинг метаданных, растановка индексов
        """
        with open(self.filename, 'rb') as f:
            file = f.read()
            pos = 4  # первые 4 байта занимает 'fLaC'
            is_last = False
            while not is_last:
                is_last, type_of_block, size = self.parse_metadata_block_header(file[pos:pos + 4])
                positions = (pos + 4, pos + 4 + size)
                if type_of_block == 0:
                    """
                    Этот блок содержит информацию обо всем потоке, такую как частота дискретизации, 
                    количество каналов, общее количество отсчетов и т.д. Он должен присутствовать в качестве 
                    первого блока метаданных в потоке. 
                    Могут последовать и другие блоки метаданных, а те, которые декодер не понимает, он пропустит.
                    """
                    self.positions[STREAMINFO] = positions
                elif type_of_block == 4:
                    """
                    Этот блок предназначен для хранения списка понятных человеку пар имя/значение. 
                    Значения кодируются с использованием UTF-8. Это реализация спецификации комментария 
                    Vorbis (без бита кадрирования). Это единственный официально поддерживаемый механизм тегирования 
                    во FLAC. В потоке может быть только один блок VORBIS_COMMENT. В некоторой внешней документации 
                    комментарии Vorbis называются тегами FLAC, чтобы избежать путаницы.
                    """
                    self.positions[VORBIS_COMMENT] = positions
                elif type_of_block == 6:
                    """
                    Этот блок предназначен для хранения изображений, связанных с файлом, чаще всего обложек 
                    с компакт-дисков. В файле может быть более одного блока PICTURE. Формат изображения аналогичен 
                    кадру APIC в ID3v2. Блок PICTURE имеет тип, MIME-тип и описание UTF-8, например ID3v2, 
                    и поддерживает внешние ссылки через URL (хотя это не рекомендуется). Различия заключаются 
                    в том, что для поля описания нет ограничения уникальности, а тип MIME является обязательным. 
                    Блок FLAC PICTURE также включает в себя разрешение, глубину цвета и размер палитры, 
                    чтобы клиент мог искать подходящее изображение без необходимости сканировать их все.
                    """
                    if PICTURE not in self.positions:
                        self.positions[PICTURE] = [positions]
                    else:
                        self.positions[PICTURE].append(positions)
                elif type_of_block == 5:
                    self.positions[CUESHEET] = positions
                elif type_of_block == 3:
                    self.positions[SEEKTABLE] = positions
                pos += size + 4
        return pos

    def parse_cuesheet(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions[CUESHEET]
            block = file[begin:end]
        cuesheet = {}
        cuesheet[MEDIA_CATALOG_NUMBER] = block[0:128].decode()
        cuesheet[LEAD_IN_SAMPLES] = int.from_bytes(block[128:136],
                                                     byteorder='big')
        cuesheet[CORRESPONDS_TO_CD] = int(bin(block[136])[2])
        number_of_tracks = block[395]
        cuesheet[TRACKS] = []
        pos = 396
        for i in range(0, number_of_tracks):
            cuesheet[TRACKS].append({})
            cuesheet[TRACKS][i][OFFSET] = int.from_bytes(block[pos:pos + 8],
                                                             byteorder='big')
            cuesheet[TRACKS][i][TRACK_NUMBER] = block[pos + 8]
            cuesheet[TRACKS][i][ISRC] = block[pos + 9:pos + 21].decode()
            cuesheet[TRACKS][i][IS_AUDIO] = int(bin(block[pos + 21])
                                                    .zfill(8)[2])
            cuesheet[TRACKS][i][PRE_EMPHASIS] = int(bin(block[pos + 21])
                                                        .zfill(8)[3])
            number_of_track_points = block[pos + 35]
            pos += 36
            cuesheet[TRACKS][i][TRACK_INDEX] = []
            for j in range(0, number_of_track_points):
                cuesheet[TRACKS][i][TRACK_INDEX].append({})
                cuesheet[TRACKS][i][TRACK_INDEX][j][OFFSET] = int.from_bytes(block[pos:pos + 8], byteorder='big')
                cuesheet[TRACKS][i][TRACK_INDEX][j][INDEX_POINT_NUMBER] = block[pos + 8]
                pos += 12
        return cuesheet

    def parse_seektable(self):
        with open(self.filename, 'rb') as f:
            file = f.read()
            begin, end = self.positions[SEEKTABLE]
            block = file[begin:end]
        pos = 0
        seektable = []
        counter = 0
        while pos + 17 < len(block):
            seektable.append({})
            seektable[counter]['first sample'] = block[pos:pos + 8]
            seektable[counter][OFFSET] = block[pos + 8:pos + 16]
            seektable[counter]['number of samples'] = block[pos + 16:pos + 18]
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
                if not (b'\xff\xfb' >= file[pos:pos + 2] >= b'\xff\xf8'):
                    pos += 1
                else:
                    counter += 1
                    try:
                        # TODO исправить говнокод по обработке фрейма
                        block_size, sample_rate, channels, sample_size, offset, frame_sample_number \
                            = self.parse_one_frame(file, pos, counter)
                    except ValueError:
                        counter -= 1
                        pos += 1
                        continue
                    self.frames.append({})
                    self.frames[counter][BLOCK_SIZE] = block_size
                    self.frames[counter][SAMPLE_RATE] = sample_rate
                    self.frames[counter][CHANNELS] = channels
                    self.frames[counter][SAMPLE_SIZE] = sample_size
                    self.frames[counter][OFFSET] = pos
                    pos = offset
                    if self.blocking_strategy:
                        self.frames[counter][SAMPLE_NUMBER] = frame_sample_number

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
            block_size = self.streaminfo[BLOCK_MAXSIZE]
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
            sample_rate = self.streaminfo[RATE]
        if 1 <= sample_rate <= 11:
            sample_rate = constants.sample_rate[sample_rate]
        if sample_rate == 12:
            sample_rate = file[pos + 4 + length + block_size_len]
            sample_rate_len = 1
        if sample_rate == 13:
            sample_rate = int.from_bytes(file[pos + 4 + length + block_size_len:
                                              pos + 6 + length + block_size_len],
                                         byteorder='big') / 1000
            sample_rate_len = 2
        if sample_rate == 14:
            sample_rate = int.from_bytes(file[pos + 4 + length + block_size_len:
                                              pos + 6 + length + block_size_len],
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
            sample_size = self.streaminfo[BITS_PER_SAMPLE]
        else:
            sample_size = constants.sample_size[sample_size]

        if self.blocking_strategy == 0:
            if frame_sample_number != counter:
                raise ValueError()

        end_pos = pos + 4 + block_size_len + sample_rate_len + length
        if file[end_pos] != crc8.get_crc(file[pos:end_pos]):
            raise ValueError()
        pos += 5 + block_size_len + sample_rate_len + length
        return block_size, sample_rate, channels, sample_size, pos, frame_sample_number

    def save_picture(self):
        """
        :return: сохраняет картинку
        """
        with open('{0}pic.{1}'.format(self.filename.split('.')[0], self.picture[0]['extension']), 'wb') as f:
            f.write(self.picture[0]['pic'])

    def make_text(self):
        """
        :return: вся инфа по стриму аудиоданных
        """
        text = constants.text.format(self.streaminfo[BLOCK_MINSIZE],
                                     self.streaminfo[BLOCK_MAXSIZE],
                                     self.streaminfo[FRAME_MINSIZE],
                                     self.streaminfo[FRAME_MAXSIZE],
                                     self.streaminfo[RATE],
                                     self.streaminfo[CHANNELS],
                                     self.streaminfo[BITS_PER_SAMPLE],
                                     self.streaminfo[SAMPLES_IN_FLOW])
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
                pictures += constants.pic_text. \
                    format(str(i + 1),
                           self.picture[i]['picture type'],
                           self.picture[i]['mime type'],
                           self.picture[i]['description'],
                           self.picture[i]['width'],
                           self.picture[i]['height'],
                           self.picture[i]['color depth'],
                           self.picture[i]['number of colors'])
            text += pictures

        if len(self.cuesheet) > 0:
            cuesheet_text = constants.cuesheet_text.format(self.cuesheet
                                               [MEDIA_CATALOG_NUMBER],
                                               self.cuesheet
                                               [LEAD_IN_SAMPLES],
                                               self.cuesheet
                                               [CORRESPONDS_TO_CD])
            for i in range(0, len(self.cuesheet[TRACKS])):
                track_text = constants.track_text.format(
                    self.cuesheet[TRACKS][i][TRACK_NUMBER],
                    self.cuesheet[TRACKS][i][OFFSET],
                    self.cuesheet[TRACKS][i][ISRC],
                    self.cuesheet[TRACKS][i][IS_AUDIO],
                    self.cuesheet[TRACKS][i][PRE_EMPHASIS]
                )
                for j in range(0, len(self.cuesheet[TRACKS]
                                      [i][TRACK_INDEX])):
                    track_index_text = '\n{0}. Offset {1}'.format(
                        self.cuesheet[TRACKS][i][TRACK_INDEX][j][INDEX_POINT_NUMBER],
                        self.cuesheet[TRACKS][i][TRACK_INDEX][j][OFFSET]
                    )
                    track_text += track_index_text
                cuesheet_text += track_text
            text += cuesheet_text
        return text

    def save_frames_text(self):
        text = ''
        for i in range(0, len(self.frames)):
            text += constants.frames_text.format(i,
                                                 self.frames[i][OFFSET],
                                                 self.frames[i][BLOCK_SIZE],
                                                 self.frames[i][SAMPLE_RATE],
                                                 self.frames[i][CHANNELS],
                                                 self.frames[i][SAMPLE_SIZE])
            if self.blocking_strategy:
                text += constants.sample_number_text.format(self.frames[i][SAMPLE_NUMBER])
            text += '\n\n'
        with open(self.filename.split('.')[0] + ' frames.txt', 'w') as f:
            f.write(text)
