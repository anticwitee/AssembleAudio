

def ProcessWav(file_name):

    import os

    header = []
    data = []

    wav_file = open(file_name, 'rb')

    first_16 = wav_file.read(16)
    header.append(bytes(first_16))
    header.append(bytes(b'(\x00\x00\x00'))
    wav_file.seek(20)  #skips over SubChunk1size (for now)
    format_numC_sRate_bRate = wav_file.read(12)
    header.append(bytes(format_numC_sRate_bRate))

    #fin at 31/32

    block_size_format = wav_file.read(4)
    header.append(bytes(block_size_format))

    #Above is all WAV RIFF Data

    #Data
    wav_file.seek(40)
    b_size_of_file = wav_file.read(4)
    i_size_of_file = int.from_bytes(b_size_of_file, byteorder='little')
    sound_data = wav_file.read()

    if len(sound_data) == i_size_of_file:
        data.append(sound_data)
    else:
        print("There appears to be a sizing issue.")

    wav_file.close()

    header = ExpandHeader(header, file_name)

    return (header, data)

def ExpandHeader(header, file_name):
    #Takes the 'header' info obtained from a source WAV file
    #and expands it to include neccessary info in a SCOTT header.

    import os

    empty_bytes_4 = bytes([0,0,0,0])

    scott_sep = [0 for i in range(24)]
    scott_sep = bytes(scott_sep)
    header.append(scott_sep)

    #Scott Headers

    #"Scot" and the 424 constant

    header.append(bytes("scot", "ASCII"))
    header.append(bytes([168, 1, 0, 0]))

    #Scratchpad
    header.append(empty_bytes_4)

    #Title
    #44 bytes -1 ish
    title = bytes("This is the title", "ASCII")
    header.append(title)
    title_padding = bytes(" " * (43 - len(title)), "ASCII")
    header.append(title_padding)

    #non-aligned cut number
    cut_num = bytes("8822", "ASCII")
    header.append(cut_num)
    header.append(bytes([0]))

    #approx duration
    header.append(bytes("00:09", "ASCII"))

    #cue-in
    header.append(empty_bytes_4)

    #total_length
    header.append(bytes([9,0,90,0]))

    #Start/End Date (6 bytes each, MMDDYY)
    header.append(bytes("031107989898", "ASCII"))

    #Start/End Hour. Hardcoded (1am-11pm)
    header.append(bytes([129, 151]))

    #"digital"? Possibly just padding
    header.append(bytes([0]))

    #SampleRate (44100 ---> 441) HARDCODED for now
    header.append(bytes([1, 185]))

    #Mono/Stereo (ASCII)
    header.append(bytes("S", "ASCII"))

    #Compression....?
    header.append(bytes([10]))

    #eomstrt (no clue)
    header.append(bytes([88, 0, 0, 0]))

    #34 bytes of optional params
    header.append(bytes([0 for i in range(34)]))

    #priorcat --> postcopy is ASCII (with padding in between)
    header.append(bytes(" " * 7, "ASCII"))
    header.append(bytes([0]))
    header.append(bytes(" " * 7, "ASCII"))

    #130 bytes of optional params
    header.append(bytes([0 for i in range(130)]))


    #ASCII Artist + etc
    header.append(bytes(" " * 68, "ASCII"))

    #Intro, End, Year, padding
    header.append(bytes("00" + (" " * 5), "ASCII"))

    #Padding
    header.append(bytes([0]))

    #Hour/Date Recorded (Hex/ASCII)
    header.append(bytes([91]))
    header.append(bytes("031107", "ASCII"))

    #Mpegbitrate/pitch
    header.append(empty_bytes_4)

    #playlevel?
    header.append(bytes([255,255]))

    #lenvalid?
    header.append(bytes([128]))

    #filelength - BETTER METHOD req
    file_size = os.stat(file_name).st_size
    header.append((file_size).to_bytes(4, byteorder='little'))

    #newplaylev??
    header.append((33768).to_bytes(2, byteorder='little'))

    #optional params
    header.append(bytes([0 for x in range(61)]))

    #fact
    header.append(bytes("fact", "ASCII"))

    #the "4" constant
    header.append(bytes([4, 0, 0,0]))

    #num_audio_samples HARDCODED
    header.append((389632).to_bytes(4, byteorder='little'))

    #data
    header.append(bytes("data", "ASCII"))

    #filelength - 512
    header.append((file_size - 512).to_bytes(4, byteorder='little'))

    return header


def WriteScottFile(header, data, output_name):
    """Takes in a list of byte objects 'header',
        a list of byte objects 'data' and an 'output_name'
        which is the new scott file. The scott file contains
        the byte objects in header and data."""

    scott_file = open(output_name, 'wb')

    for item in header:
        scott_file.write(item)

    for item in data:
        scott_file.write(item)

    scott_file.close()


def ConvertScott(source, dst):
    #Assumes WAV

    header, data = ProcessWav(source)
    WriteScottFile(header, data, dst)


def info(file_name):

    wav_file = open(file_name, 'rb')
    header_stop = 512
    pointer = 4
    total_read = 0
    while total_read < header_stop:
        print(wav_file.read(pointer))
        print("-----------------------ADDR: ", str(total_read) + "---", end = '')
        total_read += pointer
        print(total_read-1)
    wav_file.close()



def GetWavInfo(file_name):
    """Gets the WAV info required for Scott files.

    """

    import os

    file_len = os.stat(file_name).st_size

    wav_file = open(file_name, 'rb')
    wav_file.seek(16)
    sub_chunk1_size_pcm = wav_file.read(4)
    print("PCM: ", sub_chunk1_size_pcm)
    pcm_2 = wav_file.read(2)
    num_channels = wav_file.read(2)
    sample_rate = wav_file.read(4)
    byte_rate = wav_file.read(4)
    block_align = wav_file.read(2)
    bits_per_sample = wav_file.read(2)

    print("PCM_2: ", pcm_2)
    print("Num channels: ", num_channels)
    print("Sample_Rate", sample_rate)
    print("Byte_rate: ", byte_rate)
    print("Block Align: ", block_align)
    print("bits_per_sample: ", bits_per_sample)

    print(int.from_bytes(pcm_2, byteorder='little'))




def SimpleReWrite(source, dst):

    source = open(source, 'rb')
    dst = open(dst, 'wb')

    for line in source:
        dst.write(line)

    source.close()
    dst.close()


def Corrupt(file_name, output):

    corrupt_file = open(file_name, 'rb')
    ayy = corrupt_file.read(40)
    new_file = open(output, 'wb')
    new_file.write(bytes(ayy))
    new_file.write(bytes(23))
    corrupt_file.seek(42)
    ayy2 = corrupt_file.read()
    new_file.write(bytes(ayy2))


    new_file.close()
    corrupt_file.close()


def DataTest(source, dst):
    #Quick function to see if data
    #transfer between SCOTT files is possible

    source_file = open(source, 'rb')
    dst_file = open(dst, 'wb')

    header = source_file.read(512)
    print(header)
    dst_file.write(bytes(header))

    source_file.seek(512)
    data = source_file.read()
    dst_file.write(bytes(data))

    source_file.close()
    dst_file.close()
