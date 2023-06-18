import math
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
import glob
import os
import re


cwd = os.getcwd()


from midi2audio import FluidSynth
from pydub import AudioSegment
path_sf2 = os.path.join(cwd, "*.sf2")
sf2_file = glob.glob(path_sf2)[0]
fs = FluidSynth(sf2_file)
target_dBFS = -20


paths_midi_files_path = os.path.join(cwd, "MIDI Files IN", "*.mid")
paths_midi_files = glob.glob(paths_midi_files_path)
midi_file_names = [path.replace("\\", "/").split("/")[-1] for path in paths_midi_files]

if midi_file_names = []:
    sys.exit('\nPlease place at least one MIDI (".mid") file within the "MIDI Files IN" folder.')

print("midi_file_names: ", midi_file_names)

#A "MIDI Files OUT" folder is created to contain the tempo adjusted
#and/or merged MIDI files.
if not os.path.exists(os.path.join(cwd, "MIDI Files OUT")):
    os.makedirs(os.path.join(cwd, "MIDI Files OUT"))

ratio = 1.66


tempo_substitution_done = False
tempo = None

def apply_same_tempo(related_midi_file_names, midi_file_names, paths_midi_files):
    for i in range(len(related_midi_file_names)):
        for j in range(len(related_midi_file_names[i])):
            mid = MidiFile(os.path.join(cwd, "MIDI Files IN", related_midi_file_names[i][j]))
            different_track_beat_values = []
            different_track_tempos = []
            first_tempo_found = False
            for k in range(len(mid.tracks)):
                tick_adjustment_ratio = None
                for l in range(len(mid.tracks[k])):
                    tempo_hits = []
                    message_string = str(mid.tracks[k][l])
                    if "set_tempo" in message_string:
                        tempo_hits = re.findall(r"tempo=(\d+),", message_string)
                        if tempo_hits != []:
                            tempo_hits = [int(tempo) for tempo in tempo_hits]
                            different_track_tempos.append([k, l, tempo_hits[0]])
                            if first_tempo_found:
                                mid.tracks[k][l] = MetaMessage("text", text='Previous "set_tempo value: "' + str(tempo_hits[0]))
                            else:
                                first_tempo_found = True
                    if tempo_hits and len(different_track_tempos) > 1 and different_track_tempos[-2][2] != different_track_tempos[-1][2]:
                        tick_adjustment_ratio = 1- different_track_tempos[-2][2]/different_track_tempos[-1][2]
                        print("tick_adjustment_ratio: ", tick_adjustment_ratio)

                    if tick_adjustment_ratio and r"note_" in message_string:
                        time = int(re.findall(r"time=(\d+)", message_string)[0])
                        message_string = re.sub(r"(time=\d+)",  "time=" + str(math.floor(time/tick_adjustment_ratio)), message_string)
                        note_on_off = re.findall(r"(note_\w+)", message_string)[0]
                        message_string = ", ".join(re.sub(note_on_off, "'" + note_on_off + "'", message_string).split(" "))
                        print("message_string: ", message_string)
                        mid.tracks[k][l] = eval("Message(" + message_string + ")")
            new_file_name = related_midi_file_names[i][j][:-4] + " (one tempo).mid"
            for k in range(len(midi_file_names)):
                print("midi_file_names[k], related_midi_file_names[i][j]: ", midi_file_names[k], related_midi_file_names[i][j])
                if midi_file_names[k] == related_midi_file_names[i][j]:
                    paths_midi_files[k] = os.path.join(cwd, "MIDI Files IN", new_file_name)
                    midi_file_names[k] = new_file_name
                    mid.save(paths_midi_files[k])
                    fs.midi_to_audio(paths_midi_files[k], paths_midi_files[k][:-4] + '.wav')
                    song_audiosegment = AudioSegment.from_wav(paths_midi_files[k][:-4] + '.wav')
                    delta_dBFS = target_dBFS - song_audiosegment.dBFS
                    song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
                    song_audiosegment.export(paths_midi_files[k][:-4] + '.mp3', format="mp3", bitrate="320k")
                    os.remove(paths_midi_files[k][:-4] + '.wav')
                    with open("midi_tracks (after changes).txt", "a+") as f:
                        f.write(str(mid))
            related_midi_file_names[i][j] = new_file_name
    return related_midi_file_names, midi_file_names, paths_midi_files




print("\nmidi_file_names: ", midi_file_names)
related_midi_file_names = []
for i in range(len(midi_file_names)):
    #The midi file name is appended to the "file_names" list
    #The '.replace("\\", "/")' method is used to ensure Windows
    #compatibility.
    file_name = re.sub(r"\A(\d+-)", "", midi_file_names[i])
    related_midi_file_names_list_comprehension = [fn for fn in midi_file_names if file_name]
    if not related_midi_file_names_list_comprehension:
        related_midi_file_names.append([[file_name]])
    elif (related_midi_file_names_list_comprehension and
    related_midi_file_names_list_comprehension not in related_midi_file_names):
        related_midi_file_names.append(related_midi_file_names_list_comprehension)

for i in range(len(related_file_names)):
    ticks_per_beat_related_files = []
    for j in range(len(related_file_names[j])):
        #The midi file name is appended to the "file_names" list
        #The '.replace("\\", "/")' method is used to ensure Windows
        #compatibility.
        file_name = re.sub(r"\A(\d+-)", "", related_file_names[i][j])
        mid = MidiFile(os.path.join(cwd, "MIDI Files IN", related_file_names[i][j]))
        print("\ni, file_name: ", i, file_name)
        if related_file_names[i][j][0] == "0":
            ticks_per_beat_reference = mid.ticks_per_beat
            print("\nticks_per_beat_reference: ", ticks_per_beat_reference)
        else:
            ticks_per_beat_related_files.append(mid.ticks_per_beat)

        related_midi_file_names, midi_file_names, paths_midi_files = apply_same_tempo(related_midi_file_names, midi_file_names, paths_midi_files)

        reference_file_name = [fn for fn in midi_file_names if file name in fn and fn[0] == "0"]
        related_midi_file_names = [fn for fn in midi_file_names if file_name in fn and fn[0] != "0"]

        if reference_file_name:
            starting_ticks_per_beat = ticks_per_beat_reference
        elif len(related_file_names[i]) > 1:
            starting_ticks_per_beat = ticks_per_beat_related_files[0]
        else:
            starting_ticks_per_beat = None

        if starting_ticks_per_beat:
            for i in range(len(related_midi_file_names)):
                for j in range(len(related_midi_file_names[i])):
                     if ticks_per_beat_related_files[i][j] != starting_ticks_per_beat:
                        mid = MidiFile(os.path.join(cwd, "MIDI Files IN", related_midi_file_names[i][j]))
                        mid.ticks_per_beat = starting_ticks_per_beat
                        ticks_per_beat_correction_ratio = ticks_per_beat_related_files[i]/starting_ticks_per_beat
                        for k in range(len(mid.tracks)):
                            for l in range(len(mid.tracks[k])):
                                message_string = str(mid.tracks[k][l])




# for i in range(len(related_midi_file_names)):
#     ticks_per_beat_reference = None
#     ticks_per_beat = dict()
#     for j in range(len(related_midi_file_names[i])):
#         print("\nrelated_midi_file_names[i][j][0]: ", related_midi_file_names[i][j][0])
#         ticks_per_beat[related_midi_file_names[i][j]] = mid.ticks_per_beat
#         track_tempos = []
#         for k in range(len(mid.tracks)):
#             for l in range(len(mid.tracks[k])):
#                 if "set_tempo" in str(mid.tracks[j][k]):
#                     tempo_string = str(mid.tracks[j][k])
#                     tempo_hits = re.findall(r"tempo=(\d+),", tempo_string)
#                     if tempo_hits != []:
#                         track_tempos.append(tempo_hits)
#         print("\ntrack_tempos: ", track_tempos)
#         print("\nticks_per_beat: ", ticks_per_beat)






#OLD CODE
            # print(ticks_per_beat_1, ticks_per_beat_2)
            # print(mid.tracks)
            # for j in range(len(mid.tracks)):
            #     for k in range(len(mid.tracks[j])):
            #         #if tempo_substitution_done and time_signature_substitution_done:
            #         if tempo_substitution_done:
            #             mid.save(midi_files[i])
            #             return tempo, time_signature
            #         elif "set_tempo" in str(mid.tracks[j][k]):
            #             if i > 0 and tempo:
            #                 print("\noriginal set_tempo: ", mid.tracks[j][k])
            #                 mid.tracks[j][k] = eval("mido." + tempo)
            #                 tempo_substitution_done = True
            #             else:
            #                 reference_tempo_string = str(mid.tracks[j][k])
            #                 tempo_hits = re.findall(r"tempo=(\d+),", reference_tempo_string)
            #                 print("tempo_hits: ", tempo_hits)
            #                 if tempo_hits != []:
            #                     reference_tempo = int(tempo_hits[0])
            #                     tempo = re.sub(r"(tempo=\d+,)", "tempo=" + str(round(reference_tempo * ratio)) + "," , str(mid.tracks[j][k]))
            #                     print("tempo: ", tempo)

                    # elif "time_signature" in str(mid.tracks[j][k]):
                    #     if i > 0 and time_signature:
                    #         print("\noriginal time_signature: ", mid.tracks[j][k])
                    #         mid.tracks[j][k] = time_signature
                    #         time_signature_substitution_done = True
                    #     else:
                    #         time_signature = mid.tracks[j][k]
