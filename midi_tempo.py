## TODO:
#1- test with unmatched files


import math
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage, merge_tracks
import glob
import os
import re
from midi2audio import FluidSynth
from pydub import AudioSegment



cwd = os.getcwd()
path_sf2 = os.path.join(cwd, "*.sf2")
sf2_file = glob.glob(path_sf2)[0]
fs = FluidSynth(sf2_file)
#Should you want to normalize the volume of your tracks, you could then pass
#in the "normalization:target dBFS" argument when running the code, with "target dBFS"
#being your target decibels relative to full scale (or dBFS for short). The default
#target dBFS is set to -20 dB and will change to any number you provide after the colon.
#The code will then perform average amplitude normalization according to the difference
#between the target dBFS and that of the audio track being normalized. This difference
#will then be used to apply gain correction to the audiosegment.
target_dBFS = -20

#The MIDI files within the "MIDI Files IN" folder in which you will place
#the MIDI files to be merged and/or tempo-adjusted, are retrieved using
#a "glob.glob()" method. Their file name without the root path (the "replace"
#method preceding the "split('/')" makes the code compatible with Windows
#paths. The paths are stored in the "midi_file_names" variable).
paths_midi_files_path = os.path.join(cwd, "MIDI Files IN", "*.mid")
paths_midi_files = glob.glob(paths_midi_files_path)
midi_file_names = [path.replace("\\", "/").split("/")[-1] for path in paths_midi_files]

#Should there be no MIDI files within the "MIDI Files IN" folder, you will be
#prompted to add some.
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
    cumulative_ticks = 0
    merge_midi = False
    file_name = re.sub(r"\A(\d+-)", "", related_midi_file_names[i][0])
    for j in range(len(related_midi_file_names[i])):
        mid = MidiFile(os.path.join(cwd, "MIDI Files IN", related_midi_file_names[i][j]))

        """REMOVE"""
        # with open("What is going on.txt", "a+") as what:
        #     what.write("\n\ni, j, related_midi_fil_names[i][0]:\n "  + str(i) + " " +  str(j) + " " + related_midi_file_names[i][j] + "\n\n")
        #     what.write(str(mid))
        midi_file_altered = False
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

        if (merge_midi == False and len(related_midi_file_names[i]) > 2 or
        len(related_midi_file_names[i]) > 1 and related_midi_file_names[i][0][0] != "0"):
            merge_midi = True
            mid_merged = MidiFile(ticks_per_beat = ticks_per_beat_reference)

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
                        #For each new track within a MIDI file, only the first "set_tempo" MetaMessage
                        #instance is kept, and the subsequent ones are changed for the following text:
                        if first_tempo_found:
                            mid.tracks[k][l] = (MetaMessage("text", text='Previous "set_tempo value: "' +
                            str(tempo_hits[0])))
                        elif (tempo_reference and len(different_track_tempos) > 1 and
                        tempo_reference != different_track_tempos[-1][2]):
                            message_string = re.sub(r"(tempo=\d+)", "tempo=" +
                            str(tempo_reference), message_string)
                            mid.tracks[k][l] = eval("mido." + message_string)
                            first_tempo_found = True
                        else:
                            first_tempo_found = True
                        if (tempo_reference and len(different_track_tempos) > 1 and
                        tempo_reference != different_track_tempos[-1][2]):
                            tick_adjustment_ratio = different_track_tempos[-1][2]/tempo_reference*ticks_per_beat_correction_ratio
                            if k == 0:
                        elif (tempo_reference and len(different_track_tempos) > 1 and
                        tempo_reference == different_track_tempos[-1][2]):
                            tick_adjustment_ratio = ticks_per_beat_correction_ratio
                            if k == 0:

                if r"note_" in message_string:
                    time = int(re.findall(r"time=(\d+)", message_string)[0])
                    message_string = re.sub(r"(time=\d+)",  "time=" + str(math.floor(time*tick_adjustment_ratio)), message_string)
                    note_on_off = re.findall(r"(note_\w+)", message_string)[0]
                    message_string = ", ".join(re.sub(note_on_off, "'" + note_on_off + "'", message_string).split(" "))
                    mid.tracks[k][l] = eval("Message(" + message_string + ")")
                    midi_file_altered = True

        if (j == 0 and merge_midi == True and related_midi_file_names[i][0][0] != "0" or
        j == 1 and merge_midi == True and related_midi_file_names[i][0][0] == "0"):
            for k in range(len(mid.tracks)):
                mid_merged.tracks.append(mid.tracks[k])
            cumulative_ticks = math.floor(mid.length * 1000000 / tempo_reference * ticks_per_beat_reference)
        elif j > 0 and merge_midi == True:
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
                            break
                return mid

            mid = adjust_starting_tick(mid, cumulative_ticks)

            cumulative_ticks += math.floor(mid.length * 1000000 / tempo_reference * ticks_per_beat_reference)
            for k in range(len(mid.tracks)):
                mid_merged.tracks.append(mid.tracks[k])

        # elif (len(related_midi_file_names[i]) == 1 or len(related_midi_file_names[i]) == 2 and
        # related_midi_file_names[i][0][0] != "0" and midi_file_altered):
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
        MIDI_file_name = file_name[:-4] + " (merged).mid"
        path_merged_midi = os.path.join(cwd, "MIDI Files OUT", MIDI_file_name)
        mid_merged.save(path_merged_midi)
        fs.midi_to_audio(path_merged_midi, path_merged_midi[:-4] + '.wav')
        song_audiosegment = AudioSegment.from_wav(path_merged_midi[:-4] + '.wav')
        delta_dBFS = target_dBFS - song_audiosegment.dBFS
        song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
        song_audiosegment.export(path_merged_midi[:-4] + '.mp3', format="mp3", bitrate="320k")
        os.remove(path_merged_midi[:-4] + '.wav')

        """REMOVE"""
        with open("midi_tracks (after changes, merged).txt", "w+") as f:
            f.write(str(mid_merged))

    else:
        for j in range(len(related_midi_file_names[i])):
            MIDI_file_name = related_midi_file_names[i][0]
            if midi_file_name[0] != "0":
                break
    if related_midi_file_names[i][0][0] == "0":

        def find_first_note_and_tempo(mid, first_note):
            found_first_note = False
            found_tempo = False
            note_duration = 0
            for j in range(len(mid.tracks)):
                for k in range(len(mid.tracks[j])):
                    if found_first_note and found_tempo:
                        return note_duration, note, tempo
                    message_string = str(mid.tracks[j][k])
                    if found_tempo == False and "tempo=" in message_string:
                        tempo = int(re.findall(r"tempo=(\d+)", message_string)[0])
                        found_tempo = True
                    elif not first_note and not found_first_note and "note_" in message_string:
                        note_duration += int(re.findall(r"time=(\d+)", message_string)[0])
                        note = int(re.findall(r"note=(\d+)", message_string)[0])
                    elif first_note and not found_first_note and "note_" in message_string:
                        note = int(re.findall(r"note=(\d+)", message_string)[0])
                        if note == found_note:
                            note_duration += int(re.findall(r"time=(\d+)", message_string)[0])
                    elif (note and not found_first_note and "note_" in message_string and
                     int(re.findall(r"note=(\d+)", message_string)[0]) == note):
                        note_duration += int(re.findall(r"time=(\d+)", message_string)[0])
                        if "note_off" in message_string or "velocity=0" in message_string:
                            found_first_note = True
                    elif note:
                        note_duration += int(re.findall(r"time=(\d+)", message_string)[0])


        mid = MidiFile(os.path.join(cwd, "MIDI Files IN", related_midi_file_names[i][1]))
        note_duration, note, tempo = find_first_note_and_tempo(mid, None)

        mid_reference = MidiFile(os.path.join(cwd, "MIDI Files IN", related_midi_file_names[i][0]))
        note_duration_reference, note_reference, tempo_reference = find_first_note_and_tempo(mid_reference)








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
