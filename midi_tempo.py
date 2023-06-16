import math
import mido
from mido import Message, MidiFile, MidiTrack
import glob
import os
import re



cwd = os.getcwd()
paths_midi_files_path = os.path.join(cwd, "MIDI Files IN", "*.mid")
paths_midi_files = glob.glob(paths_midi_files_path)
midi_file_names = [path.replace("\\", "/").split("/")[-1] for path in paths_midi_files]

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
            for k in range(len(mid.tracks)):
                tick_adjustment_ratio = None
                for l in range(len(mid.tracks[k])):
                    beat_value_hits = []
                    tempo_hits = []
                    message_string = str(mid.tracks[k][l])
                    #print("message_string: ", message_string)
                    #print(r"note_" in message_string)
                    if "notated_32nd_notes_per_beat" in message_string:
                        beat_value_hits = re.findall(r"notated_32nd_notes_per_beat=(\d+),", message_string)
                        if beat_value_hits != []:
                            beat_value_hits = [int(beat_value) for beat_value in beat_value_hits]
                            different_track_beat_values.append([k, l, beat_value_hits[0]])
                    if "set_tempo" in message_string:
                        tempo_hits = re.findall(r"tempo=(\d+),", message_string)
                        if tempo_hits != []:
                            tempo_hits = [int(tempo)/32 for tempo in tempo_hits]
                            different_track_tempos.append([k, l, tempo_hits[0]])
                    if tempo_hits and len(different_track_tempos) > 1 and different_track_tempos[-2][2] != different_track_tempos[-1][2]:
                        if beat_value_hits and len(different_track_beat_values) > 1 and different_track_beat_values[-2][2] != different_track_beat_values[-1][2]:
                            tick_adjustment_ratio = (different_track_tempos[-2][2] * different_track_beat_values[-2][2] /
                            different_track_tempos[-1][2] * different_track_beat_values[-1][2])
                        else:
                            tick_adjustment_ratio = different_track_tempos[-2][2]/different_track_tempos[-1][2]
                            print("tick_adjustment_ratio: ", tick_adjustment_ratio)

                    elif beat_value_hits and len(different_track_beat_values) > 1 and different_track_beat_values[-2][2] != different_track_beat_values[-1][2]:
                        if tempo_hits and len(different_track_tempos) > 1 and different_track_tempos[-2][2] != different_track_tempos[-1][2]:
                            tick_adjustment_ratio = (different_track_tempos[-2][2] * different_track_beat_values[-2][2] /
                            different_track_tempos[-1][2] * different_track_beat_values[-1][2])
                        else:
                            tick_adjustment_ratio = (different_track_tempos[-1][2] * different_track_beat_values[-2][2] /
                            different_track_tempos[-1][2] * different_track_beat_values[-1][2])
                    if tick_adjustment_ratio and r"note_" in message_string:
                        time = int(re.findall(r"time=(\d+)", message_string)[0])
                        message_string = re.sub(r"(time=\d+)",  "time=" + str(math.floor(tick_adjustment_ratio*time)), message_string)
                        note_on_off = re.findall(r"(note_\w+)", message_string)[0]
                        message_string = ", ".join(re.sub(note_on_off, "'" + note_on_off + "'", message_string).split(" "))
                        print("message_string: ", message_string)
                        mid.tracks[k][l] = eval("Message(" + message_string + ")")
            new_file_name = related_midi_file_names[i][j][:-4] + " (one tempo).mid"
            for k in range(len(midi_file_names)):
                print("midi_file_names[k], related_midi_file_names[i][j]: ", midi_file_names[k], related_midi_file_names[i][j])
                if midi_file_names[k] == related_midi_file_names[i][j]:
                    paths_midi_files[k] = os.path.join(cwd, "MIDI Files OUT", new_file_name)
                    mid.save(paths_midi_files[k])
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
    print("\ni, file_name: ", i, file_name)
    if midi_file_names[i][0] == "0":
        reference_file_name = midi_file_names[i]
        mid = MidiFile(os.path.join(cwd, "MIDI Files IN", midi_file_names[i]))
        ticks_per_beat_reference = mid.ticks_per_beat

        print("\nticks_per_beat_reference: ", ticks_per_beat_reference)
    related_midi_file_names_list_comprehension = [fn for fn in midi_file_names if file_name in fn and fn[0] != "0"]
    if not related_midi_file_names_list_comprehension:
        related_midi_file_names.append([[file_name]])
    elif related_midi_file_names_list_comprehension not in related_midi_file_names:
        related_midi_file_names.append(related_midi_file_names_list_comprehension)

if related_midi_file_names != []:
    related_midi_file_names, midi_file_names, paths_midi_files = apply_same_tempo(related_midi_file_names, midi_file_names, paths_midi_files)

related_midi_file_names = list(related_midi_file_names)
print("\nrelated_midi_file_names: ", related_midi_file_names)

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
