def ConvertScott(source, dst, title_str, id_num, artist):
    #Assumes WAV

    try:
        header, data = ProcessWav(source, title_str, id_num, artist)
        WriteScottFile(header, data, dst)
    except IOError:
        print("---ConvertScott: File {0} cannot be opened.".format(source))



def WriteScottFile(header, data, output_name):
    """Takes in a list of byte objects 'header',
        a list of byte objects 'data' and an 'output_name'
        which is the new scott file. The scott file contains
        the byte objects in header and data."""

    from os.path import exists

    if not exists(output_name):
        with open(output_name, 'wb') as scott_file:
            for item in header:
                scott_file.write(item)

            for item in data:
                scott_file.write(item)
    else:
        print("File {} already exists.".format(output_name))




def ProcessWav(file_name, title_str, id_num, artist):
    """Gather necessary info from a RIFF WAV header.

    """

    #Could use WAVE library for simplified reading

    header = []
    data = []

    with open(file_name, 'rb') as wav_file:
        #riff
        riff = wav_file.read(4)
        header.append(bytes(riff))

        #file size - 8
        src_f_size = wav_file.read(4)
        f_size = int.from_bytes(src_f_size, byteorder='little') + 476
        header.append((f_size - 8).to_bytes(4, byteorder='little'))

        #WAVE, fmt
        header.append(wav_file.read(8))

        #Some constant
        header.append(bytes(b'(\x00\x00\x00'))

        #skips over SubChunk1size (for now)
        wav_file.seek(20)

        #NumChannels, Sample rate, bitrate, blocksize, format
        rates_misc = wav_file.read(16)
        header.append(bytes(rates_misc))

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


    ExpandHeader(header, file_name, f_size, title_str, id_num, artist)

    return (header, data)

def ExpandHeader(header, file_name, f_size, title_str, id_num, artist):
    #Takes the 'header' info obtained from a source WAV file
    #and expands it to include neccessary info in a SCOTT header.

    import wave

    f = wave.open(file_name, "rb")
    num_c = f.getnchannels()
    samp_width = f.getsampwidth()
    samp_rate =  f.getframerate()
    f.close()

    padd_1 = bytes([0])
    padd_4 = bytes([0,0,0,0])

    scott_sep = [0 for i in range(24)]
    scott_sep = bytes(scott_sep)
    header.append(scott_sep)





    #Scott Headers

    #"Scot" and the 424 constant

    scot = bytes("scot", "ASCII")
    const_424 = bytes([168, 1, 0, 0])

    #Scratchpad
    scratchpad = padd_4

    #Title                                          ATTENTION
    #43 bytes
    title = bytes(title_str, "ASCII")
    title_padding = bytes(" " * (43 - len(title)), "ASCII")









    #non-aligned cut number                    ATTENTION
    cut_num = bytes(id_num, "ASCII")
    align_1 = padd_1

    #approx duration THIS GETS OVERWRITTEN (GOOD, BUT)
    apprx_dur = bytes("00:09", "ASCII")

    #cue-in
    cue_in = padd_4

    #total_length                            ATTENTION
    total_length = bytes([9,0,90,0])

    #Start/End Date (6 bytes each, MMDDYY)    ATTENTION
    s_e_dates = bytes("031107111220", "ASCII")

    #Start/End Hour. Hardcoded (1am-11pm)       ATTENTION
    s_e_hour = bytes([129, 151])

    #"digital"? Possibly just padding
    digital = padd_1

    #SampleRate (/100)
    rate_div_100 = (samp_rate // 100).to_bytes(2, byteorder='little')

    #Mono/Stereo (ASCII)                        ATTENTION
    if num_c == 1:
        c_type = "M"
    else:
        c_type = "S"
    c_type = bytes(c_type, "ASCII")

    #Compression....?
    compres = bytes([10])

    #eomstrt (no clue)
    eomstrt = bytes([88, 0, 0, 0])

    #34 bytes of optional params
    opt_params = bytes([0 for i in range(34)])













    #priorcat --> postcopy is ASCII (with padding in between)
    priorcat = bytes(" " * 7, "ASCII")
    align_2 = padd_1
    postcat = bytes(" " * 7, "ASCII")

    #130 bytes of optional params
    opt_params_2 = bytes([0 for i in range(130)])


    #ASCII Artist + etc                               ATTENTION
    artist_etc = bytes(artist + " " * (68 - len(artist)), "ASCII")

    #Intro, End, Year, padding
    intro_yr = bytes("00" + (" " * 5), "ASCII")

    #Padding
    align_3 = padd_1

    #Hour/Date Recorded (Hex/ASCII)
    hour_rec = bytes([91])
    date_rec = bytes("031107", "ASCII")

    #Mpegbitrate/pitch
    pitch = padd_4

    #playlevel?
    playlevel = bytes([255,255])

    #lenvalid?
    lenvalid = bytes([128])

    #FULL file size
    full_f_size = (f_size).to_bytes(4, byteorder='little')

    #newplaylev??
    newplaylev = (33768).to_bytes(2, byteorder='little')









    #optional params
    opt_params_3 = bytes([0 for x in range(61)])

    #fact
    fact = bytes("fact", "ASCII")

    #the "4" constant
    const_4 = bytes([4, 0, 0,0])

    #NumSamples = NumBytes / (NumChannels * BitsPerSample / 8)
    #Doesn't quite work with mono
    num_samples = (f_size - 512) // (num_c * samp_width)
    b_num_samples = (num_samples).to_bytes(4, byteorder='little')

    #data
    data = bytes("data", "ASCII")

    #filelength - 512
    size_512 = (f_size - 512).to_bytes(4, byteorder='little')


    header.extend([scot, const_424, scratchpad, title, title_padding,
                  cut_num, align_1, apprx_dur, cue_in, total_length,
                  s_e_dates, s_e_hour, digital, rate_div_100, c_type,
                  compres, eomstrt, opt_params, priorcat, align_2,
                  postcat, opt_params_2, artist_etc, intro_yr, align_3,
                  hour_rec, date_rec, pitch, playlevel, lenvalid, 
                  full_f_size, newplaylev, opt_params_3, fact, const_4,
                  b_num_samples, data, size_512])


def info(file_name):

    try:
        with open(file_name, 'rb') as wav_file:
            header_stop = 512
            pointer = 4
            total_read = 0
            while total_read < header_stop:
                print(wav_file.read(pointer))
                print("-----------------------ADDR: ", str(total_read) + "---", end = '')
                total_read += pointer
                print(total_read-1)
    except IOError:
        print("---Info: File {0} cannot be opened.".format(file_name))


def SimpleReWrite(source, dst):

    source = open(source, 'rb')
    dst = open(dst, 'wb')

    for line in source:
        dst.write(line)

    source.close()
    dst.close()
