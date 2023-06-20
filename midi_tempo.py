## TODO:
#1- test with unmatched files

#1- Cap the start of each MIDI file at a certain number of microseconds to avoid awkward silences
#2- Adjust velocity


import math
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage, merge_tracks
import glob
import os
import re
from midi2audio import FluidSynth
from pydub import AudioSegment
import sys



cwd = os.getcwd()
#Should you want to normalize the volume of your tracks, you could then pass
#in the "normalization:target dBFS" argument when running the code, with "target dBFS"
#being your target decibels relative to full scale (or dBFS for short). The default
#target dBFS is set to -20 dB and will change to any number you provide after the colon.
#The code will then perform average amplitude normalization according to the difference
#between the target dBFS and that of the audio track being normalized. This difference
#will then be used to apply gain correction to the audiosegment.
target_dBFS = -20


tempo_adjustment = None

if len(sys.argv) > 1:
    #The "try/except" statement will
    #intercept any "ValueErrors" and
    #ask the users to correctly enter
    #the desired values for the variables
    #directly after the colon separating
    #the variable name from the value.
    try:
        for i in range(1, len(sys.argv)):
            if sys.argv[i][:9].strip().lower() == "normalize":
                normalize_split = [element for element in sys.argv[i].strip().split(":") if element != ""]
                if len(normalize_split) > 1:
                    target_dBFS = int(normalize_split[1].strip())
            elif sys.argv[i][:5].strip().lower() == "tempo":
                tempo_split = [element for element in sys.argv[i].strip().split(":") if element != ""]
                if len(tempo_split) > 1:
                    tempo_adjustment = int(tempo_split[1].strip())
    except:
        pass



#The function "audio_parameters()" extracts the parenthesized values of the SoundFont
#number and "target_dBFS" from the end of the SoundFont files (".sf2") and audio files.
#This will allow to pair up MIDI files with their respective SoundFont files, and to
#override any default or user selected values of "target_dBFS" that would otherwise
#apply to all audio files. Any "target_dBFS" values found at the end of SoundFont files
#will apply to all the MIDI files of matching SoundFont number. For example, the target
#dBFS of -25 dB from the SountFont file named "Piano(1 -25).sf2" would apply to all of
#the midi files of the following format: "MIDI_file_name(1).mid". Furthermore, you can
#further fine-tune the normalization process by specifying a target dBFS for a given
#audio file, by including it within parentheses at the end of the file name. For instance,
#the MIDI file with the following file name "MIDI_file_name(-28 1).mid" would have a
#target dBFS of -28 dB, in spite of the "Piano(1 -25).sf2" file which would still apply the
#-25 dB target dBFS to the other MIDI files of the same SoundFont number (1). For other
#audio file types than midi, just add the target dBFS within parentheses at the end of
#the file name (ex: "mp3_file_name(-27).mp3") and the default -20 dB or any other value
#that you passed in with the "normalize:" argument would still apply to the other audio
#files that do not end with such a parenthesized expression.
def audio_parameters(file_name):
    dBFStarget_soundfont_matches_split = None
    #The r"[(](-\d+[ \d+]*|[\d+ ]*-\d+|\d+)[)]\Z" pattern will look for the presence of
    #a parenthesized expression at the end ("\Z") of "file name" that either contains
    #a negative integer ("-\d+") by itself or preceded or followed by a positive integer
    #("\d+") with one space in-between the two instances. For example: the file name
    #extracted from a MIDI file "Harpsichord Sonata in D, catalog K 141, by (it)Domenico
    #Scarlatti(it)(-20 3)" would return "[-20, 3]", with "-20" being the new value of the
    #target dBFS ("target_dBFS"), and "3" being the SoundFont file number included in
    #the working folder. Another match that the "finditer" function can return is a
    #single positive integer by itself ("\d+"), to indicate the SoundFont file number,
    #with the "target_dBFS" being the default one or the one specified after the
    #"normalize:" argument.
    dBFStarget_soundfont_hits = re.finditer(r"[(](-\d+[ \d+]*|[\d+ ]*-\d+|\d+)[)]\Z", file_name)
    #The strip() method will remove spaces after the opening parenthesis and before
    #the closing parenthesis. For example: ( 2 -30 ) will return (2 -30)
    #(without the parentheses). The contents of the parentheses will then be split
    #along spaces to separate the SoundFont number from the target dBFS and then
    #each resulting string will be converted into integers using a map() method.
    dBFStarget_soundfont_matches =[m.group(1).strip().split(" ") for m in dBFStarget_soundfont_hits if m.group(1)]
    dBFStarget_soundfont_matches = [list(map(int, element)) for element in dBFStarget_soundfont_matches]
    if dBFStarget_soundfont_matches:
        #As the "list(map())" method introduced a new layer of lists, it is
        #now removed by indexing the first element of "dBFStarget_soundfont_matches".
        dBFStarget_soundfont_matches = dBFStarget_soundfont_matches[0]
    return dBFStarget_soundfont_matches


path_sf2 = os.path.join(cwd, "*.sf2")
sf2_files = glob.glob(path_sf2)
if sf2_files == []:
    sys.exit('\n\nPlease include at least one SoundFont (".sf2") file within your working folder.')
else:
    list_soundfonts_dBFStarget = []
    len_sf2_files = len(sf2_files)
    for i in range(len_sf2_files):
        sf2_file_name = "".join(sf2_files[i].split(".")[:-1]).replace("\\", "/").split("/")[-1]
        dBFStarget_soundfont_file = audio_parameters(sf2_file_name)
        if dBFStarget_soundfont_file:
            #The elements of the list "dBFStarget_soundfont_file" are sorted in reverse order,
            #in order to have the positive SoundFont number first, followed by the negative
            #target dBFS.
            list_soundfonts_dBFStarget.append(sorted(dBFStarget_soundfont_file, reverse = True))

    #If "list_soundfonts_dBFStarget = []" this means that none of the "sf2" files in the working folder
    #have parenthesized SoundFont numbers nor target dBFS values. This is only acceptable if there is
    #only one "sf2" file within the working folder, as all of the MIDIs could be rendered from that file.
    #If "list_soundfonts_dBFStarget != []" and each item of the list "sf2_files" has returned a positive
    #number corresponding to the SoundFont number (or if there was only one file in "sf2_files"), then the
    #corresponding "sf2" file path is concatenated to each element of "list_soundfonts_dBFStarget" before
    #sorting it along the first element, corresponding to the SountFont number if "len_sf2_files" is
    #greater than one.
    if list_soundfonts_dBFStarget == [] and len_sf2_files == 1:
        list_soundfonts_dBFStarget = [sf2_files[0]]
    elif (list_soundfonts_dBFStarget != [] and len(list_soundfonts_dBFStarget) == len_sf2_files and
    (len_sf2_files == 1 or (len_sf2_files > 1 and all([element[0] > 0 for element in list_soundfonts_dBFStarget])))):
        list_soundfonts_dBFStarget = [list_soundfonts_dBFStarget[i] + [sf2_files[i]] for i in range(len_sf2_files)]
        list_soundfonts_dBFStarget.sort(key = lambda x:x[0])
    else:
        sys.exit('\n\nPlease add the SoundFont file number in parentheses at the end of the SoundFont file name. ' +
        'This will allow the code to match the SoundFont number of the MIDI files to that of the SoundFont file.' +
        'For example: "midi_file(1).mid" would be rendered using the SoundFont file "piano_soundfont(1).sf2".' +
        'Should you also want to specify a target dBFS for a given SoundFont file that will be applied to all ' +
        'MIDI files of the matching SoundFont number, enter the negative decibel value (without units) in the same ' +
        'parenthesis, separated by a space from the SoundFont number. For example: "midi_file(1).mid" would be rendered ' +
        'using the SoundFont file "piano_soundfont(1 -30).sf2", with a target dBFS of -30 dB. Furthermore, should you ' +
        'like to specify a target dBFS that would apply to a single MIDI file, simply enter it along with the SoundFont ' +
        'number within parentheses at the end of the MIDI file name. For instance, the target dBFS of -35 dB would be ' +
        'used to render the MIDI file with the following name "other_midi_file(-35 1).mid", and the -30 dB target dBSF of ' +
        'the "piano_soundfont(1 -30).sf2" would then only apply to "midi_file(1).mid".')


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



related_midi_file_names = ([[re.sub(r"\A(\d+.\d+-)", "", midi_file_names[i]),
re.sub(r"\A(\d+-)|\A(\d+.\d+-\d+-)|\A(\d+.\d+-)", "", midi_file_names[i]),
midi_file_names[i]] for i in range(len(midi_file_names))])
print("\n\n1-related_midi_file_names: ", related_midi_file_names)
related_midi_file_names.sort()
print("\n\n2-related_midi_file_names: ", related_midi_file_names)

first_files = [file for file in related_midi_file_names if file[0][0:2] == "0-"]
if not first_files:
    first_files = [file for file in related_midi_file_names if file[0][0:2] == "1-"]
if first_files:
    new_related_midi_file_names = []
    starting_index = 0
    for i in range(len(first_files)):
        new_related_midi_file_names.append([])
        for j in range(starting_index, len(related_midi_file_names), len(first_files)):
            new_related_midi_file_names[-1].append(related_midi_file_names[j][2])
        starting_index += 1
    related_midi_file_names = new_related_midi_file_names
else:
    duplicate_file_names = sum([related_midi_file_names.count(related_file_names[i][1]) for i in range(len(related_file_names))])
    if duplicate_file_names > 0:
        sys.exit('\nPlease precede the identical file names with the sequence number and a hyphen. For example: ' +
        '"1-Identical_file_name.mid", "2-Identical_file_name.mid". Should you have a reference MIDI file that you will ' +
        'be using to automatically adjust the tempo of the merged file, prefix its file name with ' +
        'a zero and a hyphen ("0-Identical_file_name").')

    related_midi_file_names = [[file[2]] for file in related_midi_file_names]

print("\n\n3-related_midi_file_names: ", related_midi_file_names)


for i in range(len(related_midi_file_names)):
    different_track_tempos = []
    ticks_per_beat_current_file = None
    ticks_per_beat_reference = None
    tempo_reference = None
    cumulative_ticks = 0
    merge_midi = False
    file_name = re.sub(r"\A(\d+-)|\A(\d+.\d+-\d+-)|\A(\d+.\d+-)", "", related_midi_file_names[i][0])
    for j in range(len(related_midi_file_names[i])):


        if related_midi_file_names[i][j][0] != "0":
        #The variable "old_target_dBFS", initialized to "None" for
        #every new song in "song_list", will store the initial
        #value of "target_dBFS" before giving precedence to any
        #values of "target_dBFS" found in the SoundFont (".sf2")
        #or audio file names. Upon rendering the song, the value
        #of "target_dBFS" will be reverted back to that of "old_target_dBFS",
        #in order to preserve the general settings defined when passing
        #in the "normalize:" argument or the default value of "target_dBFS"
        #of -20 dB.
        old_target_dBFS = None
        #The variable "soundfont_number", initialized to "None" for
        #every new song in "song_list", will contain the parenthesized
        #sound font number found at the end of the SoundFont (".sf2") and
        #corresponding MIDI (".mid") files. Its value will be updated to that
        #of the SoundFont file found in the working folder, should there only
        #be one "sf2" file in that location.
        soundfont_number = None
        #Should you have provided a value for "target_dBFS" and/or SoundFont number
        #(for MIDI files specifically) for a specific song within parentheses at the end
        #of the file name, this information would be extracted at this point.
        try:
            dBFStarget_soundfont = audio_parameters(related_midi_file_names[i][j])
            if dBFStarget_soundfont or len(list_soundfonts_dBFStarget) == 1:
                #Cycling through every element of the list "dBFStarget_soundfont", returned
                #by the "audio_parameters()" function. If the the value of the element is
                #positive, it is stored in "soundfont_number", as any other values returned
                #by the function would be negative and correspond to the updated value of
                #"target_dBFS" for this audio track.
                for j in range(len(dBFStarget_soundfont)):
                    if dBFStarget_soundfont[j] >= 0:
                        soundfont_number = dBFStarget_soundfont[j]
                    elif dBFStarget_soundfont[j] < 0:
                        old_target_dBFS = target_dBFS
                        target_dBFS = dBFStarget_soundfont[j]
                #Should the audio track be a MIDI file and the "soundfont_number"
                #not be addigned, given that the MIDI file did not end in a parenthesized
                #positive number (ex: "midi_file_name(-25).mid"), and since there has to
                #be at least one SoundFont file in the working folder a this point (because
                #otherwise the above code would have run ("sys.exit('\n\nPlease include at
                #least one SoundFont (".sf2") file within your working folder.')"), it can
                #be deduced that the MIDI files correspond to the first (or only) element
                #of list_soundfonts_dBFStarget. Should you have placed multiple SoundFont
                #files within the working folder containing a parenthesized positive
                #"soundfont_number" value at the end of their names, the code would still
                #select the first of these, and you would need to ensure that the proper
                #SoundFont was selected. Otherwise, you would need to add the SoundFont
                #information at the end of your MIDI file name (ex: "midi_file_name(1 -25).mid").
                if file_extensions[i] == "mid" and soundfont_number == None:
                    for j in range(len(list_soundfonts_dBFStarget[0])):
                        if isinstance(list_soundfonts_dBFStarget[0][j], int)  and  list_soundfonts_dBFStarget[0][j] >= 0:
                            soundfont_number = list_soundfonts_dBFStarget[0][j]
                            break
            #The following "for" loop will extract the parenthesized "soundfont_number"
            #and "target_dBFS" values found at the end of the SoundFont "sf2" file names that
            #were returned by the "dBFStarget_soundfont_file = audio_parameters(sf2_file_name)"
            #code above and then stored within the "list_soundfonts_dBFStarget" list, along
            #with the corresponding path of the "sf2" files.
            #A "FluidSynth" object is instantiated from the "sf2" file path at index 2 of
            #an element of "list_soundfonts_dBFStarget" of which the "soundfont_number"
            #matches that of the MIDI file being rendered at index "i" of the "for i in
            #range(len_song_list)" loop. As a reminder, the individual elements of
            #"list_soundfonts_dBFStarget" contain in sequence the "soundfont_number",
            #"target_dBFS" and "sf2" file path for a given SoundFont, with the possibility
            #of only containing one, or the other, or none of "soundfont_number" and "target_dBFS"
            #(the latter case being if the "sf2" didn't contain any parenthesized information,
            #ex: "Piano.sf2").
            fs = None
            for j in range(len(list_soundfonts_dBFStarget)):
                #Should the element of "list_soundfonts_dBFStarget" under
                #investigation have a length of three or more, it means that
                #it contains in sequence values of "soundfont_number", "target_dBFS"
                #and the "sf2" file path for that SoundFont file. Provided that
                #the "sf2" "soundfont_number" matches that of the MIDI file, these
                #values are then stored in the corresponding variables, with
                #"target_dBFS" only being updated if its value is "None", meaning
                #that the MIDI file didn't contain a parenthesized "target_dBFS"
                #value that would otherwise take precedence over any "target_dBFS"
                #specified in the "sf2" file name.
                if len(list_soundfonts_dBFStarget[j]) > 2:
                    if soundfont_number == list_soundfonts_dBFStarget[j][0]:
                        fs = FluidSynth(list_soundfonts_dBFStarget[j][2])
                        if old_target_dBFS == None:
                            old_target_dBFS = target_dBFS
                            target_dBFS = list_soundfonts_dBFStarget[j][1]
                        break
                #Should the current element of "list_soundfonts_dBFStarget"
                #under investigation have a length of two, it means that it
                #contains either "soundfont_number" (a positive integer) or
                #"target_dBFS" (a negative integer), followed by the path of
                #the "sf2" file. The "if" and "elif" statements deal with
                #these possibilities, with the "soundfont_number" being checked
                #first in case a matching "soundfont_number" to that of the
                #current MIDI file can be found.
                elif len(list_soundfonts_dBFStarget[j]) == 2:
                    if (list_soundfonts_dBFStarget[j][0] >= 0 and
                    soundfont_number == list_soundfonts_dBFStarget[j][0]):
                        fs = FluidSynth(list_soundfonts_dBFStarget[j][1])
                        break
                    #The "elif" statement only applies should there only be
                    #one SoundFont file within the working folder and the
                    #parenthesized value at the end of the "sf2" file name
                    #is negative, meaning that it designates the value of
                    #"target_dBFS" for that SoundFont file. Once again,
                    #the value of "target_dBFS" is only updated if that
                    #of "old_target_dBFS" be "None", in order to give
                    #precedence to the "target_dBFS" found in the MIDI
                    #file name, as mentioned above.
                    elif (len_sf2_files == 1 and
                    list_soundfonts_dBFStarget[j][0] < 0):
                         fs = FluidSynth(list_soundfonts_dBFStarget[j][1])
                         if old_target_dBFS == None:
                             old_target_dBFS = target_dBFS
                             target_dBFS = list_soundfonts_dBFStarget[j][0]
            #As there is at least one SoundFont file within the working
            #folder at this point in the code, should a "FluidSynth" object
            #not yet have been instantiated, it is instantiated now using the
            #first (or only) "sf2" file in the "sf2_files" list. This will
            #ensure that the MIDI songs are rendered and that you will be able
            #to check if the correct "sf2" was selected. This would give reliable
            #results should only one "sf2" file be in the working folder and
            #should all of the MIDI files require be rendered using that
            #SoundFont file. In this case, you wouldn't need to provide parenthesized
            #values of "soundfont_number" at the end of the SoundFont (".sf2") and
            #MIDI (".mid") file names. In all other cases, you should include this
            #information in the SoundFont and MIDI file names.
            if not fs:
                fs = FluidSynth(sf2_files[0])
        except Exception as e:
            sys.exit('\n\nThere was a problem when running the code: \n' + str(e))





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
                            mid.tracks[k][l] = (MetaMessage("text", text='Previous "tempo value: "' +
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
                        elif (tempo_reference and len(different_track_tempos) > 1 and
                        tempo_reference == different_track_tempos[-1][2]):
                            tick_adjustment_ratio = ticks_per_beat_correction_ratio

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

        elif (len(related_midi_file_names[i]) == 1 or len(related_midi_file_names[i]) == 2 and
        related_midi_file_names[i][0][0] == "0" and midi_file_altered):
            new_file_name = related_midi_file_names[i][j][:-4] + " (one tempo).mid"
            for k in range(len(midi_file_names)):
                if midi_file_names[k] == related_midi_file_names[i][j]:
                    paths_midi_files[k] = os.path.join(cwd, "MIDI Files OUT", new_file_name)
                    midi_file_names[k] = new_file_name
                    mid.save(paths_midi_files[k])
                    fs.midi_to_audio(paths_midi_files[k], paths_midi_files[k][:-4] + '.wav')
                    song_audiosegment = AudioSegment.from_wav(paths_midi_files[k][:-4] + '.wav')
                    delta_dBFS = target_dBFS - song_audiosegment.dBFS
                    song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
                    song_audiosegment.export(paths_midi_files[k][:-4] + '.mp3', format="mp3", bitrate="320k")
                    os.remove(paths_midi_files[k][:-4] + '.wav')
                    break

    if merge_midi == True:
        MIDI_file_name = file_name[:-4] + " (merged).mid"
        path_merged_midi = os.path.join(cwd, "MIDI Files OUT", MIDI_file_name)
        mid_merged.save(path_merged_midi)
        fs.midi_to_audio(path_merged_midi, path_merged_midi[:-4] + '.wav')
        song_audiosegment = AudioSegment.from_wav(path_merged_midi[:-4] + '.wav')
        if target_dBFS:
            delta_dBFS = target_dBFS - song_audiosegment.dBFS
            song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
        song_audiosegment.export(path_merged_midi[:-4] + '.mp3', format="mp3", bitrate="320k")
        os.remove(path_merged_midi[:-4] + '.wav')

        """REMOVE"""
        with open("midi_tracks (after changes, merged).txt", "w+") as f:
            f.write(str(mid_merged))


    def find_first_note_and_tempo(mid, first_note):
        found_first_note = False
        found_tempo = False
        note_duration = 0
        note = None
        for j in range(len(mid.tracks)):
            for k in range(len(mid.tracks[j])):
                if found_first_note and found_tempo:
                    return note_duration, note, tempo
                message_string = str(mid.tracks[j][k])
                if not found_tempo and "tempo=" in message_string:
                    tempo = int(re.findall(r"tempo=(\d+)", message_string)[0])
                    found_tempo = True
                elif not first_note and note_duration == 0 and "note_" in message_string:
                    note_duration += int(re.findall(r"time=(\d+)", message_string)[0])
                    note = int(re.findall(r"note=(\d+)", message_string)[0])
                elif (first_note and note_duration == 0 and "note_" in message_string and
                first_note == int(re.findall(r"note=(\d+)", message_string)[0])):
                    note_duration += int(re.findall(r"time=(\d+)", message_string)[0])
                    note = first_note
                elif (note and "note_" in message_string and
                 note == int(re.findall(r"note=(\d+)", message_string)[0]) and
                 ("note_off" in message_string or "velocity=0" in message_string)):
                    note_duration += int(re.findall(r"time=(\d+)", message_string)[0])
                    found_first_note = True
                elif note:
                    note_duration += int(re.findall(r"time=(\d+)", message_string)[0])

    def apply_tempo_correction(mid, tempo_adjustment):
        for j in range(len(mid.tracks)):
            for k in range(len(mid.tracks[j])):
                message_string = str(mid.tracks[j][k])
                if "set_tempo" in message_string:
                    print("\n\nmessage_string: ", message_string)
                    tempo = int(re.findall(r"tempo=(\d+),", message_string)[0])
                    print("\n\ntempo: ", tempo)
                    if isinstance(tempo_adjustment, int):
                        tempo = tempo_adjustment
                    else:
                        tempo = math.floor(tempo*tempo_adjustment)
                    print("\n\ntempo: ", tempo)
                    message_string = re.sub(r"(tempo=\d+)", "tempo=" +
                    str(tempo), message_string)
                    mid.tracks[j][k] = eval("mido." + message_string)
                    print("\n\nmid.tracks[j][k]: ", mid.tracks[j][k])
        return mid

    if os.path.exists(os.path.join(cwd, "MIDI Files OUT", MIDI_file_name)):
        mid = MidiFile(os.path.join(cwd, "MIDI Files OUT", MIDI_file_name))
    elif midi_file_altered:
        mid = MidiFile(os.path.join(cwd, "MIDI Files OUT", new_file_name))
    else:
        mid = MidiFile(os.path.join(cwd, "MIDI Files IN", related_midi_file_names[i][1]))

    if tempo_adjustment:
        if tempo_adjustment < 5000:
            def find_notated_32nd_notes_per_beat(mid):
                notated_32nd_notes_per_beat = 8
                for j in range(len(mid.tracks)):
                    for k in range(len(mid.tracks[j])):
                        message_string = str(mid.tracks[j][k])
                        if "notated_32nd_notes_per_beat=" in message_string:
                            return int(re.findall(r"notated_32nd_notes_per_beat=(\d+),", message_string)[0])

            notated_32nd_notes_per_beat = find_notated_32nd_notes_per_beat(mid)
            #microseconds/quarter-note = minute/beat * (32/notated_32nd_notes_per_beat)/4 * 60 seconds/minute * 1000000 us/second
            tempo_adjustment = math.floor(1/tempo_adjustment * (32/notated_32nd_notes_per_beat)/4 * 60000000)

        mid = apply_tempo_correction(mid, tempo_adjustment)
        MIDI_file_name = file_name[:-4] + ".mid"
        path_merged_midi = os.path.join(cwd, "MIDI Files OUT", MIDI_file_name)
        mid.save(path_merged_midi)
        fs.midi_to_audio(path_merged_midi, path_merged_midi[:-4] + '.wav')
        song_audiosegment = AudioSegment.from_wav(path_merged_midi[:-4] + '.wav')
        if target_dBFS:
            delta_dBFS = target_dBFS - song_audiosegment.dBFS
            song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
        song_audiosegment.export(path_merged_midi[:-4] + '.mp3', format="mp3", bitrate="320k")
        os.remove(path_merged_midi[:-4] + '.wav')

    elif related_midi_file_names[i][0][0] == "0":
        note_duration, note, tempo = find_first_note_and_tempo(mid, None)

        print("\n\nnote_duration: ", note_duration)

        mid_reference = MidiFile(os.path.join(cwd, "MIDI Files IN", related_midi_file_names[i][0]))
        note_duration_reference, note_reference, tempo_reference = find_first_note_and_tempo(mid_reference, note)

        print("\n\nnote_duration_reference: ", note_duration_reference)
        print("\n\nticks_per_beat_reference: ", ticks_per_beat_reference)
        print("\n\ntempo_reference: ", tempo_reference)

        note_duration_us = note_duration / ticks_per_beat_reference * tempo_reference
        note_duration_reference_us =  note_duration_reference / ticks_per_beat_reference * tempo_reference
        tempo_adjustment = note_duration_reference_us/note_duration_us

        print("\n\ntempo_adjustment: ", tempo_adjustment)

        mid = apply_tempo_correction(mid, tempo_adjustment)
        MIDI_file_name = file_name[:-4] + " (adjusted tempo).mid"
        path_merged_midi = os.path.join(cwd, "MIDI Files OUT", MIDI_file_name)
        mid.save(path_merged_midi)
        fs.midi_to_audio(path_merged_midi, path_merged_midi[:-4] + '.wav')
        song_audiosegment = AudioSegment.from_wav(path_merged_midi[:-4] + '.wav')
        if target_dBFS:
            delta_dBFS = target_dBFS - song_audiosegment.dBFS
            song_audiosegment = song_audiosegment.apply_gain(delta_dBFS)
        song_audiosegment.export(path_merged_midi[:-4] + '.mp3', format="mp3", bitrate="320k")
        os.remove(path_merged_midi[:-4] + '.wav')

        if len(related_midi_file_names) == 1:
            print("\n\nThe new MIDI file with an adjusted tempo of " +
            str(math.floor(1/(tempo_adjustment*tempo_reference) * 60000000)) + " bpm was created successfully.")
            print("The reference file had a tempo of " + str(math.floor(1/tempo_reference * 60000000)) + " bpm.")
