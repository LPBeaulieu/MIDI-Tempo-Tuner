import glob
import math
from midi2audio import FluidSynth
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
import os
from pydub import AudioSegment
import re


cwd = os.getcwd()
path_sf2 = os.path.join(cwd, "*.sf2")
sf2_file = glob.glob(path_sf2)[0]
fs = FluidSynth(sf2_file)
target_dBFS = -20

with open("midi_tracks.txt", "a+") as f:
    f.write("0-test_song.mid\n\n")
    mid = MidiFile()
    notes_per_beat = 8
    tempo_value = 500000
    for i in range(3):
        track = MidiTrack()
        mid.tracks.append(track)
        mid.tracks[i].append(MetaMessage('sequence_number', number=i, time=0))
        mid.tracks[i].append(MetaMessage('time_signature', numerator=4, denominator=4, clocks_per_click=18, notated_32nd_notes_per_beat=notes_per_beat, time=0))
        mid.tracks[i].append(MetaMessage('set_tempo', tempo=tempo_value, time=0))
        notes =[40,42,44,45,47,49,51,52]
        for note_value in notes:
            mid.tracks[i].append(Message('note_on', note=note_value, velocity=90, time=0))
            mid.tracks[i].append(Message('note_off', note=note_value, velocity=90, time=500))
        mid.tracks[i].append(MetaMessage('end_of_track'))

    f.write(str(mid))
    f.write("\n\n")

    mid.save('0-test_song.mid')
    fs.midi_to_audio('0-test_song.mid', '0-test_song.wav')
    song_audiosegment = AudioSegment.from_wav('0-test_song.wav')
    delta_dBFS = target_dBFS - song_audiosegment.dBFS
    song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
    song_audiosegment.export("0-test_song.mp3", format="mp3", bitrate="320k")
    os.remove('0-test_song.wav')

    # f.write("\n1-test_song.mid\n\n")
    # mid = MidiFile()
    # track = MidiTrack()
    # notes_per_beat = 8
    # tempo_value = 0
    # for i in range(3):
    #     tempo_value += 500000
    #     track = MidiTrack()
    #     mid.tracks.append(track)
    #     mid.tracks[i].append(MetaMessage('time_signature', numerator=4, denominator=4, clocks_per_click=18, notated_32nd_notes_per_beat=notes_per_beat, time=0))
    #     mid.tracks[i].append(MetaMessage('set_tempo', tempo=tempo_value, time=0))
    #     notes =[40,42,44,45,47,49,51,52]
    #     for note_value in notes:
    #         mid.tracks[i].append(Message('note_on', note=note_value, velocity=90, time=0))
    #         mid.tracks[i].append(Message('note_off', note=note_value, velocity=90, time=500))
    #     f.write(str(mid.tracks[i]))
    # f.write("\n\n")

    f.write("\n1-test_song.mid\n\n")
    mid = MidiFile()
    notes_per_beat = 8
    tempo_value = 0
    for i in range(3):
        tempo_value += 500000
        track = MidiTrack()
        mid.tracks.append(track)
        mid.tracks[i].append(MetaMessage('sequence_number', number=i, time=0))
        mid.tracks[i].append(MetaMessage('time_signature', numerator=4, denominator=4, clocks_per_click=18, notated_32nd_notes_per_beat=notes_per_beat, time=0))
        mid.tracks[i].append(MetaMessage('set_tempo', tempo=tempo_value, time=0))
        notes =[40,42,44,45,47,49,51,52]
        for note_value in notes:
            mid.tracks[i].append(Message('note_on', note=note_value, velocity=90, time=0))
            mid.tracks[i].append(Message('note_off', note=note_value, velocity=90, time=500))
        mid.tracks[i].append(MetaMessage('end_of_track'))
    f.write(str(mid))
    f.write("\n\n")


    mid.save('1-test_song.mid')
    fs.midi_to_audio('1-test_song.mid', '1-test_song.wav')
    song_audiosegment = AudioSegment.from_wav('1-test_song.wav')
    delta_dBFS = target_dBFS - song_audiosegment.dBFS
    song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
    song_audiosegment.export("1-test_song.mp3", format="mp3", bitrate="320k")
    os.remove('1-test_song.wav')


    # f.write("\n2-test_song.mid\n\n")
    # mid = MidiFile()
    # track = MidiTrack()
    # notes_per_beat = 4
    # tempo_value = 500000
    # for i in range(3):
    #     notes_per_beat *= 2
    #     track = MidiTrack()
    #     mid.tracks.append(track)
    #     track.append(MetaMessage('time_signature', numerator=4, denominator=4, clocks_per_click=18, notated_32nd_notes_per_beat=notes_per_beat, time=0))
    #     track.append(MetaMessage('set_tempo', tempo=tempo_value, time=0))
    #     notes =[40,42,44,45,47,49,51,52]
    #     for note_value in notes:
    #         track.append(Message('note_on', note=note_value, velocity=90, time=0))
    #         track.append(Message('note_off', note=note_value, velocity=90, time=500))
    #     f.write(str(track))
    # f.write("\n\n")
    #
    #
    # mid.save('2-test_song.mid')
    # fs.midi_to_audio('2-test_song.mid', '2-test_song.wav')
    # song_audiosegment = AudioSegment.from_wav('2-test_song.wav')
    # delta_dBFS = target_dBFS - song_audiosegment.dBFS
    # song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
    # song_audiosegment.export("2-test_song.mp3", format="mp3", bitrate="320k")
    # os.remove('2-test_song.wav')
    #
    #
    # f.write("\n3-test_song.mid\n\n")
    # mid = MidiFile()
    # track = MidiTrack()
    # notes_per_beat = 4
    # tempo_value = 0
    # for i in range(3):
    #     notes_per_beat *= 2
    #     tempo_value += 500000
    #     track = MidiTrack()
    #     mid.tracks.append(track)
    #     track.append(MetaMessage('time_signature', numerator=4, denominator=4, clocks_per_click=18, notated_32nd_notes_per_beat=notes_per_beat, time=0))
    #     track.append(MetaMessage('set_tempo', tempo=tempo_value, time=0))
    #     notes =[40,42,44,45,47,49,51,52]
    #     for note_value in notes:
    #         track.append(Message('note_on', note=note_value, velocity=90, time=0))
    #         track.append(Message('note_off', note=note_value, velocity=90, time=500))
    #     f.write(str(track))
    # f.write("\n\n")
    #
    #
    # mid.save('3-test_song.mid')
    # fs.midi_to_audio('3-test_song.mid', '3-test_song.wav')
    # song_audiosegment = AudioSegment.from_wav('3-test_song.wav')
    # delta_dBFS = target_dBFS - song_audiosegment.dBFS
    # song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
    # song_audiosegment.export("3-test_song.mp3", format="mp3", bitrate="320k")
    # os.remove('3-test_song.wav')
