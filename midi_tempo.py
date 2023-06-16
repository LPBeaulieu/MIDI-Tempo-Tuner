import mido
from mido import Message, MidiFile, MidiTrack
import glob
import os
import re



cwd = os.getcwd()
paths_midi_files_path = os.path.join(cwd, "MIDI Files IN", "*.mid")
paths_midi_files = glob.glob(paths_midi_files_path)
midi_file_names = [path.replace("\\", "/").split("/")[-1] for path in paths_midi_files]

#A "MIDI Files OUT" folder is created to contain the tempo adjusted
#and/or merged MIDI files.
if not os.path.exists(os.path.join(cwd, "MIDI Files OUT")):
    os.makedirs(os.path.join(cwd, "MIDI Files OUT"))

ratio = 1.66


tempo_substitution_done = False
tempo = None

print("\nmidi_file_names: ", midi_file_names)
related_midi_file_names = []
for i in range(len(midi_file_names)):
    #The midi file name is appended to the "file_names" list
    #The '.replace("\\", "/")' method is used to ensure Windows
    #compatibility.
    file_name = re.sub(r"\A(\d+-)", "", midi_file_names[i])
    print("\ni, file_name: ", i, file_name)
    related_midi_file_names_list_comprehension = [fn for fn in midi_file_names if file_name in fn]
    if not related_midi_file_names_list_comprehension:
        related_midi_file_names.append([[file_name]])
    elif related_midi_file_names_list_comprehension not in related_midi_file_names:
        related_midi_file_names.append(related_midi_file_names_list_comprehension)

related_midi_file_names = list(related_midi_file_names)
print("\nrelated_midi_file_names: ", related_midi_file_names)

for i in range(len(related_midi_file_names)):
    ticks_per_beat_reference = None
    ticks_per_beat = dict()
    for j in range(len(related_midi_file_names[i])):
        print("\nrelated_midi_file_names[i][j][0]: ", related_midi_file_names[i][j][0])
        mid = MidiFile(os.path.join(cwd, "MIDI Files IN", related_midi_file_names[i][j]))

        if related_midi_file_names[i][j][0] == "0":
            print(related_midi_file_names[i][j])
            ticks_per_beat_reference = mid.ticks_per_beat
            print("\nticks_per_beat_reference: ", ticks_per_beat_reference)
        else:
            ticks_per_beat[related_midi_file_names[i][j]] = mid.ticks_per_beat
            track_tempos = []
            for k in range(len(mid.tracks)):
                for l in range(len(mid.tracks[k])):
                    if "set_tempo" in str(mid.tracks[j][k]):
                        tempo_string = str(mid.tracks[j][k])
                        tempo_hits = re.findall(r"tempo=(\d+),", tempo_string)
                        if tempo_hits != []:
                            track_tempos.append(tempo_hits)
            print("\ntrack_tempos: ", track_tempos)
            print("\nticks_per_beat: ", ticks_per_beat)



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
