#!/bin/bash
# нужна утилита metaflac
# arch
# sudo pacman -S metaflac
# вся инфа `metaflac --list`
clear
printf """
STREAMINFO:
        minimum block size: %d samples
        maximum block size: %d samples
        minimum frame size: %d bytes
        maximum frame size: %d bytes
        sample rate: %d Hz
        number of channels: %d
        bits per sample: %d
        samples in stream: %d
""" $(metaflac --show-min-blocksize \
               --show-max-blocksize \
               --show-min-framesize \
               --show-max-framesize \
               --show-sample-rate \
               --show-channels \
               --show-bps \
               --show-total-samples \
               /home/mnoskov/git/flac/src/resources/Sample.flac)
