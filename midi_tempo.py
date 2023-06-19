import math
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage, merge_tracks
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

if midi_file_names == []:
    sys.exit('\nPlease place at least one MIDI (".mid") file within the "MIDI Files IN" folder.')

#A "MIDI Files OUT" folder is created to contain the tempo adjusted
#and/or merged MIDI files.
if not os.path.exists(os.path.join(cwd, "MIDI Files OUT")):
    os.makedirs(os.path.join(cwd, "MIDI Files OUT"))

tempo_substitution_done = False
tempo = None

related_midi_file_names = []
for i in range(len(midi_file_names)):
    #The midi file name is appended to the "file_names" list
    #The '.replace("\\", "/")' method is used to ensure Windows
    #compatibility.
    file_name = re.sub(r"\A(\d+-)", "", midi_file_names[i])
    related_midi_file_names_list_comprehension = [fn for fn in midi_file_names if file_name]
    if related_midi_file_names_list_comprehension:
        related_midi_file_names_list_comprehension = sorted(related_midi_file_names_list_comprehension)
        if related_midi_file_names_list_comprehension not in related_midi_file_names:
            related_midi_file_names.append(related_midi_file_names_list_comprehension)
    else:
        related_midi_file_names.append([[file_name]])

for i in range(len(related_midi_file_names)):
    different_track_tempos = []
    ticks_per_beat_current_file = None
    ticks_per_beat_reference = None
    tempo_reference = None
    merge_midi = False
    cumulative_ticks = 0
    file_name = re.sub(r"\A(\d+-)", "", related_midi_file_names[i][0])
    for j in range(len(related_midi_file_names[i])):
        mid = MidiFile(os.path.join(cwd, "MIDI Files IN", related_midi_file_names[i][j]))
        # with open("What is going on.txt", "a+") as what:
        #     what.write("\n\ni, j, related_midi_fil_names[i][0]:\n "  + str(i) + " " +  str(j) + " " + related_midi_file_names[i][j] + "\n\n")
        #     what.write(str(mid))
        midi_file_altered = False
        if (len(related_midi_file_names[i][j]) > 2 or len(related_midi_file_names[i][j]) > 1 and
            related_midi_file_names[i][j][0] != "0"):
            merge_midi = True
            mid_merged = MidiFile(ticks_per_beat = ticks_per_beat_reference)
        if j == 0:
            ticks_per_beat_reference = mid.ticks_per_beat
        else:
            ticks_per_beat_current_file = mid.ticks_per_beat
        if j > 0 and ticks_per_beat_current_file != ticks_per_beat_reference:
            mid.ticks_per_beat = ticks_per_beat_reference
            ticks_per_beat_correction_ratio = ticks_per_beat_reference/ticks_per_beat_current_file
            tick_adjustment_ratio = ticks_per_beat_correction_ratio

        else:
            ticks_per_beat_correction_ratio = 1
            tick_adjustment_ratio = ticks_per_beat_correction_ratio
        for k in range(len(mid.tracks)):
            first_tempo_found = False
            for l in range(len(mid.tracks[k])):
                tempo_hits = []
                message_string = str(mid.tracks[k][l])
                if "set_tempo" in message_string:
                    tempo_hits = re.findall(r"tempo=(\d+),", message_string)
                    if tempo_hits != []:
                        tempo_hits = [int(tempo) for tempo in tempo_hits]
                        different_track_tempos.append([k, l, tempo_hits[0]])
                        if j == 0 and k == 0:
                            tempo_reference = tempo_hits[0]
                            print("\n\ntempo_reference: ", tempo_reference)
                            print("\n\nticks_per_beat_reference: ", ticks_per_beat_reference)
                        #For each new track within a MIDI file, only the first "set_tempo" MetaMessage
                        #instance is kept, and the subsequent ones are changed for the following text:
                        if first_tempo_found:
                            mid.tracks[k][l] = (MetaMessage("text", text='Previous "set_tempo value: "' +
                            str(tempo_hits[0])))
                        elif (tempo_reference and len(different_track_tempos) > 1 and
                        tempo_reference != different_track_tempos[-1][2]):
                            message_string = re.sub(r"(tempo=\d+)", "tempo=" +
                            str(tempo_reference), message_string)
                            print("\n\nmessage_string: ", message_string)
                            #mid.tracks[k][l] = MetaMessage(message_string)
                            mid.tracks[k][l] = eval("mido." + message_string)
                            first_tempo_found = True
                        else:
                            first_tempo_found = True
                        if (tempo_reference and len(different_track_tempos) > 1 and
                        tempo_reference != different_track_tempos[-1][2]):
                            tick_adjustment_ratio = different_track_tempos[-1][2]/tempo_reference*ticks_per_beat_correction_ratio
                            if k == 0:
                                print("\n\n1-tempo_reference, different_track_tempos[-1][2]: ", tempo_reference, different_track_tempos[-1][2])
                                print("tick_adjustment_ratio: ", tick_adjustment_ratio)
                        elif (tempo_reference and len(different_track_tempos) > 1 and
                        tempo_reference == different_track_tempos[-1][2]):
                            tick_adjustment_ratio = ticks_per_beat_correction_ratio
                            if k == 0:
                                print("\n\n2-tempo_reference, different_track_tempos[-1][2]: ", tempo_reference, different_track_tempos[-1][2])
                                print("tick_adjustment_ratio: ", tick_adjustment_ratio)

                if r"note_" in message_string:
                    time = int(re.findall(r"time=(\d+)", message_string)[0])
                    message_string = re.sub(r"(time=\d+)",  "time=" + str(math.floor(time*tick_adjustment_ratio)), message_string)
                    note_on_off = re.findall(r"(note_\w+)", message_string)[0]
                    message_string = ", ".join(re.sub(note_on_off, "'" + note_on_off + "'", message_string).split(" "))
                    mid.tracks[k][l] = eval("Message(" + message_string + ")")
                    midi_file_altered = True

        print("\n\nmidi_file_altered, tick_adjustment_ratio: ", midi_file_altered, tick_adjustment_ratio)

        # if (j == 0 and merge_midi == True and related_midi_file_names[i][j][0] != "0" or
        # j > 0 and merge_midi == True and related_midi_file_names[i][0][0] == "0"):

        print("\n\n1-related_midi_file_names, merge_midi: ", related_midi_file_names, merge_midi)
        if (j == 0 and merge_midi == True and related_midi_file_names[i][0][0] != "0" or
        j == 1 and merge_midi == True and related_midi_file_names[i][0][0] == "0"):
            for k in range(len(mid.tracks)):
                mid_merged.tracks.append(mid.tracks[k])
            print("\n\nFIRST FILE MERGED!!1!1!")
            print("\n\n" + str(mid_merged))
            #mid_merged.tracks.append(merge_tracks(mid.tracks))
            cumulative_ticks = math.floor(mid.length * 1000000 / tempo_reference * ticks_per_beat_reference)
            # with open("midi_tracks (after changes, merged).txt", "a+") as f:
            #     f.write("\n\n" + related_midi_file_names[i][j] + "\n\n")
            #     f.write(str(mid))
        # elif j > 0 and merge_midi == True and related_midi_file_names[i][0][0] == "0":
        #     mid_merged.tracks.append(merge_tracks(mid.tracks))
        #     cumulative_ticks = math.floor(mid.length * 1000000 / tempo_reference * ticks_per_beat_reference)
        #     with open("midi_tracks (after changes, merged).txt", "a+") as f:
        #         f.write("\n\n" + related_midi_file_names[i][j] + "\n\n")
        #         f.write(str(mid))
        elif j > 0 and merge_midi == True:
            print("\n\n2-j, related_midi_file_names[i][j], merge_midi: ", j, related_midi_file_names[i][j], merge_midi)
            def adjust_starting_tick(mid, cumulative_ticks):
                for k in range(len(mid.tracks)):
                    for l in range(len(mid.tracks[k])):
                        message_string = str(mid.tracks[k][l])
                        if "time=" in message_string:
                            time = int(re.findall(r"time=(\d+)", message_string)[0])
                            message_string = re.sub(r"(time=\d+)",  "time=" + str(math.floor(time+cumulative_ticks)), message_string)
                            if "note_" in message_string:
                                note_on_off = re.findall(r"(note_\w+)", message_string)[0]
                                message_string = ", ".join(re.sub(note_on_off, "'" + note_on_off + "'", message_string).split(" "))
                                mid.tracks[k][l] = eval("Message(" + message_string + ")")
                            elif "MetaMessage" in message_string:
                                mid.tracks[k][l] = eval("mido." + message_string)
                            return mid

            mid = adjust_starting_tick(mid, cumulative_ticks)

            cumulative_ticks += math.floor(mid.length * 1000000 / tempo_reference * ticks_per_beat_reference)
            print("\n\nj, cumulative_ticks: ", j, cumulative_ticks)
            if len(mid_merged.tracks) > 0:
                for k in range(len(mid.tracks)):
                    mid_merged.tracks[-1].append(mid.tracks[k])
            else:
                for k in range(len(mid.tracks)):
                    mid_merged.tracks.append(mid.tracks[k])
            #mid_merged.tracks.append(merge_tracks(mid.tracks))

            # with open("midi_tracks (after changes, merged).txt", "a+") as f:
            #     f.write("\n\n" + related_midi_file_names[i][j] + "\n\n")
            #     f.write(str(mid))

        # elif midi_file_altered:
        #     new_file_name = related_midi_file_names[i][j][:-4] + " (one tempo).mid"
        #     for k in range(len(midi_file_names)):
        #         if midi_file_names[k] == related_midi_file_names[i][j]:
        #             paths_midi_files[k] = os.path.join(cwd, "MIDI Files IN", new_file_name)
        #             midi_file_names[k] = new_file_name
        #             mid.save(paths_midi_files[k])
        #             fs.midi_to_audio(paths_midi_files[k], paths_midi_files[k][:-4] + '.wav')
        #             song_audiosegment = AudioSegment.from_wav(paths_midi_files[k][:-4] + '.wav')
        #             delta_dBFS = target_dBFS - song_audiosegment.dBFS
        #             song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
        #             song_audiosegment.export(paths_midi_files[k][:-4] + '.mp3', format="mp3", bitrate="320k")
        #             os.remove(paths_midi_files[k][:-4] + '.wav')
        #             with open("midi_tracks (after changes).txt", "a+") as f:
        #                 f.write(str(mid))
        #             break
        #     related_midi_file_names[i][j] = new_file_name

    if merge_midi == True:
        path_merged_midi = os.path.join(cwd, "MIDI Files IN", file_name[:-4] + " (merged).mid")
        mid_merged.save(path_merged_midi)
        fs.midi_to_audio(path_merged_midi, path_merged_midi[:-4] + '.wav')
        song_audiosegment = AudioSegment.from_wav(path_merged_midi[:-4] + '.wav')
        delta_dBFS = target_dBFS - song_audiosegment.dBFS
        song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
        song_audiosegment.export(path_merged_midi[:-4] + '.mp3', format="mp3", bitrate="320k")
        os.remove(path_merged_midi[:-4] + '.wav')

        with open("midi_tracks (after changes, merged).txt", "w+") as f:
            f.write(str(mid_merged))









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
