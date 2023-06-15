import mido
from mido import MidiFile
import glob
import os
import re



cwd = os.getcwd()
path_midi = os.path.join(cwd, "*.mid")
midi_files = glob.glob(path_midi)

ratio = 1.66

def get_tempo(midi_files):
    tempo_substitution_done = False
    time_signature_substitution_done = False
    tempo = None
    time_signature = None
    ticks_per_beat_1 = None
    ticks_per_beat_2 = None

    if midi_files:
        midi_files.sort()
        print("midi_files: ", midi_files)
        for i in range(len(midi_files)):
            print(midi_files[i])
            mid = MidiFile(midi_files[i])
            if i == 0:
                ticks_per_beat_1 = mid.ticks_per_beat
            else:
                ticks_per_beat_2 = mid.ticks_per_beat
            print(ticks_per_beat_1, ticks_per_beat_2)
            print(mid.tracks)
            for j in range(len(mid.tracks)):
                for k in range(len(mid.tracks[j])):
                    #if tempo_substitution_done and time_signature_substitution_done:
                    if tempo_substitution_done:
                        mid.save(midi_files[i])
                        return tempo, time_signature
                    elif "set_tempo" in str(mid.tracks[j][k]):
                        if i > 0 and tempo:
                            print("\noriginal set_tempo: ", mid.tracks[j][k])
                            mid.tracks[j][k] = eval("mido." + tempo)
                            tempo_substitution_done = True
                        else:
                            reference_tempo_string = str(mid.tracks[j][k])
                            tempo_hits = re.findall(r"tempo=(\d+),", reference_tempo_string)
                            print("tempo_hits: ", tempo_hits)
                            if tempo_hits != []:
                                reference_tempo = int(tempo_hits[0])
                                tempo = re.sub(r"(tempo=\d+,)", "tempo=" + str(round(reference_tempo * ratio)) + "," , str(mid.tracks[j][k]))
                                print("tempo: ", tempo)

                    # elif "time_signature" in str(mid.tracks[j][k]):
                    #     if i > 0 and time_signature:
                    #         print("\noriginal time_signature: ", mid.tracks[j][k])
                    #         mid.tracks[j][k] = time_signature
                    #         time_signature_substitution_done = True
                    #     else:
                    #         time_signature = mid.tracks[j][k]
            print("")

print(get_tempo(midi_files))

        # tempo = get_tempo(midi_files[i])
        #
        # print(midi_files[i], tempo)
