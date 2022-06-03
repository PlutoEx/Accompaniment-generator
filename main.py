import music21
import random
import math

from mido import Message, MidiFile, MidiTrack
from psycopg2 import TimeFromTicks

progressions = [['1', '5', '6', '4'], ['4', '5', '1'], ['4', '5sus4', '5', '1'], ['1', '6', '4', '5sus4', '1'], ['1', '4', '5sus4', '1'], ['1', '4', '5', '1'], ['1', '7', '3', '6', '4', '5'], ['2', '5', '1'], ['1', '4', '5'], ['2', '5', '1'], ['1', '5', '6', '3', '4', '1', '4', '5']]
speed_of_progression = [[1, 1, 1, 1], [1, 1, 1],       [1, 2, 2, 1],             [1, 1, 2, 2, 1],               [1, 1, 1, 1],             [1, 1, 1, 1],         [1, 2, 2, 1, 2, 2],             [1, 1, 1],       [1, 1, 1],       [1, 1, 1],       [1, 1, 1, 1, 1, 1, 1, 1]]
minor_table = [['Cm', 'D*', 'Eb', 'Fm', 'Gm', 'Ab', 'Bb'], ['C#m', 'D#*', 'E', 'F#m', 'G#m', 'A', 'B'], ['Dm', 'E*', 'F', 'Gm', 'Am', 'Bb', 'C'], ['D#m', 'E#*', 'F#', 'G#m', 'A#m', 'B', 'C#'], ['Ebm', 'F*', 'Gb', 'Abm', 'Bbm', 'Cb', 'Db'], ['Em', 'F#*', 'G', 'Am', 'Bm', 'C', 'D'], ['Fm', 'G*', 'Ab', 'Bbm', 'Cm', 'Db', 'Eb'], ['F#m', 'G#*', 'A', 'Bm', 'C#m', 'D', 'E'], ['Gm', 'A*', 'Bb', 'Cm', 'Dm', 'Eb', 'F'], ['G#m', 'A#*', 'B', 'C#m', 'D#m', 'E', 'F#'], ['Abm', 'Bb*', 'Cb', 'Dbm', 'Ebm', 'Fb', 'Gb'], ['Am', 'B*', 'C', 'Dm', 'Em', 'F', 'G'], ['A#m', 'B#*', 'C#', 'D#m', 'E#m', 'F#', 'G#'], ['Bbm', 'C*', 'Db', 'Ebm', 'Fm', 'Gb', 'Ab'], ['Bm', 'C#*', 'D', 'Em', 'F#m', 'G', 'A']]
major_table = [['C', 'Dm', 'Em', 'F', 'G', 'Am', 'B*'], ['C#', 'D#m', 'E#m', 'F#', 'G#', 'A#m', 'B#*'], ['Db', 'Ebm', 'Fm', 'Gb', 'Ab', 'Bbm', 'C*'], ['D', 'Em', 'F#m', 'G', 'A', 'Bm', 'C#*'], ['Eb', 'Fm', 'Gm', 'Ab', 'Bb', 'Cm', 'D*'], ['E', 'F#m', 'G#m', 'A', 'B', 'C#m', 'D#*'], ['F', 'Gm', 'Am', 'Bb', 'C', 'Dm', 'E*'], ['F#', 'G#m', 'A#m', 'B', 'C#', 'D#m', 'E#*'], ['Gb', 'Abm', 'Bbm', 'Cb', 'Db', 'Ebm', 'F*'], ['G', 'Am', 'Bm', 'C', 'D', 'Em', 'F#*'], ['Ab', 'Bbm', 'Cm', 'Db', 'Eb', 'Fm', 'G*'], ['A', 'Bm', 'C#m', 'D', 'E', 'F#m', 'G#*'], ['Bb', 'Cm', 'Dm', 'Eb', 'F', 'Gm', 'A*'], ['B', 'C#m', 'D#m', 'E', 'F#', 'G#m', 'A#*']]

# convert note Symbol to Midi format
def symbol_to_note(symbol):
    first_note = 0
    if 'C' in symbol: first_note = 48
    elif 'D' in symbol: first_note = 50
    elif 'E' in symbol: first_note = 52
    elif 'F' in symbol: first_note = 53
    elif 'G' in symbol: first_note = 55
    elif 'A' in symbol: first_note = 57
    elif 'B' in symbol: first_note = 59
    if '#' in symbol: first_note += 1
    elif 'b' in symbol: first_note -= 1
    return first_note

# get array of notes in midi format (ex 64)
# then we normalize our accompaniment to be in one octave [48; 59]
def get_notes(symbol, type):
    first_note = symbol_to_note(symbol)
    if 'sus2' in type:
        notes = get_sus2(first_note)
    elif 'sus4' in type:
        notes = get_sus4(first_note)
    elif 'm' in symbol:
        notes = get_minor(first_note)
    elif '*' in symbol:
        notes = get_diminished(first_note)
    else:
        notes = get_major(first_note)
    for i in range(0, len(notes)):
        if notes[i] > 59:
            notes[i] -= 12
        elif notes[i] < 48:
            notes[i] += 12
    return notes

# -1 for lower +1 for high accompaniment
def change_octave(notes):
    count = 0
    for i in range(0, len(notes)):
        notes[i] += (12 * count)
    return notes

# Add notes to midi
# We can change octave/Velocity
def add_notes(notes, speed):
    VELOCITY = 64
    notes = change_octave(notes)
    for i in notes:
        new_track.append(Message('note_on', channel=0, velocity=VELOCITY, note=i, time=0))
    for i in notes:
        if i == notes[0]:
            new_track.append(Message('note_off', channel=0, note=i, velocity=VELOCITY,  time=int(mid.ticks_per_beat*2/speed)))
        else:
            new_track.append(Message('note_off', channel=0, note=i, velocity=VELOCITY, time=0))

# Walk throw Major/minor table
# We run in our progression and get Chords from this table
# Then add pressed notes to midi and check if our accompaniment is not begger than melody, if it is so just end our program
def table_walk(progression, speed):
    if key.mode == 'minor':
        for i in minor_table:
            if i[0] == (key.tonic.name + 'm'):
                for j in progression:
                    add_notes(get_notes(i[int(j[0]) - 1], j), speed[progression.index(j)])
                    if new_mid.length >= mid.length:
                        return
    elif key.mode == 'major':
        for i in major_table:
            if i[0] == (key.tonic.name):
                for j in progression:
                    add_notes(get_notes(i[int(j[0]) - 1], j), speed[progression.index(j)])
                    if new_mid.length >= mid.length:
                        return

# Randomly get one of the progression
def get_progression():
    return random.choice(progressions)

# Simple minor/major/sus2/sus4/diminished
def get_minor(first_note):
    notes = []
    notes.append(first_note)
    notes.append(first_note + 3)
    notes.append(first_note + 7)
    return notes

def get_major(first_note):
    notes = [0]*3
    notes[0] = first_note
    notes[1] = first_note + 4
    notes[2] = first_note + 7
    return notes

def get_diminished(first_note):
    notes = [0]*3
    notes[0] = first_note
    notes[1] = first_note + 3
    notes[2] = first_note + 6
    return notes

def get_sus2(first_note):
    notes = [0]*3
    notes[0] = first_note
    notes[1] = first_note + 2
    notes[2] = first_note + 7
    return notes

def get_sus4(first_note):
    notes = [0]*3
    notes[0] = first_note
    notes[1] = first_note + 5
    notes[2] = first_note + 7
    return notes

# Here First Solution without mutations just random accompaniment
def Solution():
    while new_mid.length < mid.length:
        progression = get_progression()
        speed = speed_of_progression[progressions.index(progression)]
        table_walk(progression, speed)
    new_mid.tracks.append(mid.tracks[1])
    new_mid.save("output.mid")

# Calculate Notes that can be pressed in my melody
# Using this coeficient I find right notes
def calculate_scale():
    major_coef = [2, 4, 5, 7, 9, 11, 12]
    minor_coef = [2, 3, 5, 7, 8, 10, 12]
    first_note = symbol_to_note(key.tonic.name)
    if key.mode == 'minor':
        for i in minor_coef:
            scale.append(first_note + i)
    elif key.mode == 'major':
        for i in major_coef:
            scale.append(first_note + i)
    for i in range(0, len(scale)):
        if scale[i] > 59:
            scale[i] -= 12
        elif scale[i] < 48:
            scale[i] += 12

# Calculate count of right pressed notes
# More the better
# Then I calculate average to delete not useful notes
# We can plot by average
def calculate_rate():
    avg = 0
    for i in range(0, len(rate)):
        rate[i] = 0
        for j in range(0, len(individ[i])):
            for k in range(0, len(scale)):
                if individ[i][j] == scale[k]:
                    rate[i] += 1
                    break
        avg += rate[i]
    avg /= len(rate)
    return avg

# Here I delete all individums that their rate is lower than average
# I reverse del_list to avoid mistakes while removing
def delete_lowest(avg):
    del_list = []
    for i in range (0, len(rate)):
        if rate[i] < avg:
            del_list.append(i)
    for i in reversed(del_list):
        rate.pop(i)
        individ.pop(i)
        rank.pop(i)

# Calculate rank in population
# To know which are best to choice
def calculate_rank():
    sorted = rate
    sorted.sort(reverse=True)
    for i in range (0, len(individ)):
        for j in range (0, len(sorted)):
            if rate[i] == sorted[j]:
                rank[i] = j
                break

# Here I crossing two individums
# Choicing them by TOP_INDIVID
# then randomly choice which chord I will swap
# I will create the first individum with one part from second individum
def crossing():
    for i in range(0, len(individ)):
        if rank[i] <= TOP_INDIVID:
            for j in range(0, len(individ)):
                if rank[j] <= TOP_INDIVID:
                    if len(individ) >= MAX_SUBJECTS:
                        return
                    x = random.randint(0, CNT_CHORDS - 1)
                    y = random.randint(0, CNT_CHORDS - 1)
                    notes = individ[i]
                    notes[x * 3] = individ[j][y * 3]
                    notes[x * 3 + 1] = individ[j][y * 3 + 1]
                    notes[x * 3 + 2] = individ[j][y * 3 + 2]
                    individ.append(notes)
                    rate.append(0)
                    rank.append(0)

# Add notes to Midi file
# step is 3 because in individ I contain notes not chords
def add_notes2(notes):
    VELOCITY = 64
    notes = change_octave(notes)
    for i in range(0, len(notes), 3):
        new_track2.append(Message('note_on', channel=0, velocity=VELOCITY, note=notes[i], time=0))
        new_track2.append(Message('note_on', channel=0, velocity=VELOCITY, note=notes[i + 1], time=0))
        new_track2.append(Message('note_on', channel=0, velocity=VELOCITY, note=notes[i + 2], time=0))
    for i in range(0, len(notes), 3):
        if i == 0:
            new_track2.append(Message('note_off', channel=0, note=notes[i], velocity=VELOCITY,  time=int(mid.ticks_per_beat*2)))
            new_track2.append(Message('note_off', channel=0, note=notes[i + 1], velocity=VELOCITY,  time=0))
            new_track2.append(Message('note_off', channel=0, note=notes[i + 2], velocity=VELOCITY,  time=0))
        else:
            new_track2.append(Message('note_off', channel=0, note=notes[i], velocity=VELOCITY, time=0))
            new_track2.append(Message('note_off', channel=0, note=notes[i + 1], velocity=VELOCITY, time=0))
            new_track2.append(Message('note_off', channel=0, note=notes[i + 2], velocity=VELOCITY, time=0))

# Second version of get array of notes
def get_notes2(first_note, type):
    if type == 1:
        notes = get_minor(first_note) 
    elif type == 2:
        notes = get_major(first_note)
    elif type == 3:
        notes = get_sus2(first_note)
    elif type == 4:
        notes = get_sus4(first_note)
    elif type == 5:
        notes = get_diminished(first_note)
    for j in range(0, len(notes)):
        if notes[j] > 59:
            notes[j] -= 12
        elif notes[j] < 48:
            notes[j] += 12
    return notes

# Solution more info in report
def Solution2():
    calculate_scale()
    for i in range (0, MIN_SUBJECT):
        notes = []
        for j in range (0, CNT_CHORDS):
            symbol = random.randint(48, 59)
            type = random.randint(1, 5)
            note = get_notes2(symbol, type)
            for k in note:
                notes.append(k)
        individ.append(notes)
        rate.append(0)    
        rank.append(0)
    for i in range (0, MAX_GENERATION):
        avg = math.ceil(calculate_rate())
        delete_lowest(avg)
        calculate_rank()
        crossing ()
    while mid.length > new_mid2.length:
        for i in range (0, len(individ)):
            if rank[i] <= 1:
                add_notes2(individ[i])
            if mid.length <= new_mid2.length:
                break
    new_mid2.tracks.append(mid.tracks[1])
    new_mid2.save("ArlanKuralbayevOutput3.mid")
                
            
# Input file
file = "input3.mid"

mid = MidiFile(file)
score = music21.converter.parse(file)
key = score.analyze('key')

new_mid = MidiFile()
new_mid2 = MidiFile()
new_track = MidiTrack()
new_track2 = MidiTrack()
new_mid.ticks_per_beat = mid.ticks_per_beat
new_mid2.ticks_per_beat = mid.ticks_per_beat
new_mid.tracks.append(new_track)
new_mid2.tracks.append(new_track2)
        
MAX_GENERATION = 20
MIN_SUBJECT = 200
MAX_SUBJECTS = 1000
TOP_INDIVID = 10
CNT_CHORDS = 4
individ = []
rate = []
scale = []
rank = []

#Solution()
Solution2()