def convertScott(source, dst, id_num = '0000', title_str = '', artist = ''):
    #Assumes WAV

    try:
        header, data = processWav(source, title_str, id_num, artist)
        writeScottFile(header, data, dst)
    except IOError:
        print("---ConvertScott: File {0} cannot be opened.".format(source))



def writeScottFile(header, data, output_name):
    """Takes in a list of byte objects 'header',
        a list of byte objects 'data' and an 'output_name'
        which is the new scott file. The scott file contains
        the byte objects in header and data."""

    from os.path import exists
    from os.path import splitext

    if exists(output_name):
        basename, extension = splitext(output_name)
        output_name = basename + '_new_scot' + extension
        if exists(output_name):
            print("File {} already exists.".format(output_name))
            return

    with open(output_name, 'wb') as scott_file:
        for item in header:
            scott_file.write(item)

        for item in data:
            scott_file.write(item)




def wav_File_Handler(filename, edit_list, new_name = ''):
    #Given a file, the function will determine
    #whether it is a SCOT WAV file or just a
    #regular WAV file. Based on the result,
    #it will call the appropriate function

    from os.path import join, dirname

    edit = False
    conversion = False
    try:
        with open(filename, 'rb') as wav_file:
            wav_file.seek(8)
            is_wav_file = wav_file.read(4)
            if is_wav_file == bytes('WAVE', 'ASCII'):
                wav_file.seek(60)
                scot = wav_file.read(4)
                if scot == bytes('scot', 'ASCII'):
                    edit = True
                else:
                    conversion = True
            else:
                print("Not a wav file:", is_wav_file)
    except IOError:
        print("--Wav_File_Handler Error--")

    if edit:
        return editScottWav(filename, edit_list, new_name = new_name)
    elif conversion:
        if new_name:
            path = join(dirname(filename), new_name)
            convertScott(filename, path)
        else:
            convertScott(filename, filename)

def editScottWav(file_name, edit, new_name = ''):
    #Edits the scott file 'file_name', optionally re-naming
    #the file.
    from os import rename
    from os.path import dirname, isfile, join

    addr = {"title" : 72, "year" : 406, "artist" : 335, "end" : 405,
            "note" : 369, "intro" : 403, "eom" : 152, "s_date" : 133,
            "e_date" : 139, "s_hour" : 145, "e_hour": 146}

    temp_is_scott = False
    renamed = False
    edited = False

    try:
        with open(file_name, 'rb+') as f:
            f.seek(60)
            if not f.read(4) == bytes("scot", "ASCII"):
                print("---EditScott error, {} is not a SCOTTWAV file.---".format(file_name))
            else:
                for name, data in edit:
                    f.seek(addr[name])
                    if type(data) == type("str"):
                        f.write(bytes(data, "ASCII"))
                    else:
                        #May be a more efficient way
                        num_bytes = len(str(abs(data)))
                        f.write((data).to_bytes(num_bytes, byteorder='little'))
                edited = True

    except IOError:
        print("---EditScott cannot open {}. ---".format(file_name))

    if new_name:
        try:
            #don't want to rename while file is open.
            new_f_name = join(dirname(file_name), new_name)
            if isfile(new_f_name):
                print("---EditScott file {} already exists, not renaming.----".format(new_f_name))
            else:
                rename(file_name, new_f_name)
                renamed = new_f_name
        except IOError:
            print("---EditScott Cannot rename {} to {}.---".format(file_name, new_name))

    return renamed, edited


def processWav(file_name, title_str, id_num, artist):
    """Gather necessary info from a RIFF WAV header.

    """
    #> 40 constant is just the size of the FMT chunk
    #possibly should adjust it to represent what I'm actually doing.
    #Reading info from scott file that is converted is fuked.
    #Due to indexes not lining up due to extra metadata...
    #Strip?



    import wave
    header = []
    data = []

    #Doesn't work inside ctx manager due to wave.open
    f = wave.open(file_name, 'rb')
    num_c = f.getnchannels()
    samp_width = f.getsampwidth()
    samp_rate =  f.getframerate()
    f.close()

    with open(file_name, 'rb') as wav_file:
        riff = wav_file.read(4)
        header.append(bytes(riff))

        #file size - 8
        src_f_size = wav_file.read(4)
        f_size = int.from_bytes(src_f_size, byteorder='little') + 476
        header.append((f_size - 8).to_bytes(4, byteorder='little'))

        wave_header = wav_file.read(4)
        header.append(wave_header)

        fmt_byte = bytes('fmt ', 'ASCII')

        #Loop until you meet 'fmt'
        bytes_4 = wav_file.read(4)
        while bytes_4 != fmt_byte:
            bytes_4 = wav_file.read(4)

        header.append(bytes_4)

        #scot_sep could fluctuate to account for some extra params
        src_fmt_size = wav_file.read(4)
        fmt_size = int.from_bytes(src_fmt_size, byteorder='little')

        #FMT PCM size
        header.append((16).to_bytes(4, byteorder='little'))

        # counter = fmt_size
        # amount = counter // 4
        # while counter > 0:
        #     header.append(wav_file.read(4))
        #     counter -= amount

        #Standard PCM, might try to account for small amounts of extra-params
        header.append(wav_file.read(16))

        #sanity check
        iterations = 0
        bytes_4 = wav_file.read(4)
        data_byte = bytes('data', 'ASCII')
        while bytes_4 != data_byte:
            if iterations < 1000:
                iterations += 1
                bytes_4 = wav_file.read(4)
            else:
                print("Wow.")
                break

        #Sound data (Block 3)
        src_data_size = wav_file.read(4)
        i_data_size = int.from_bytes(src_data_size, byteorder='little')

        ExpandHeader(header, num_c, samp_width, samp_rate, i_data_size, f_size, title_str, id_num, artist)

        sound_data = wav_file.read()
        if not len(sound_data) == i_data_size:
            print("Footer information detected.")
        data.append(sound_data)

    return (header, data)

def ExpandHeader(header, num_c, samp_width, samp_rate, data_size, f_size, title_str, id_num, artist):
    #Takes the 'header' info obtained from a source WAV file
    #and expands it to include neccessary info in a SCOTT header.

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
    num_samples = (data_size) // (num_c * samp_width)
    b_num_samples = (num_samples).to_bytes(4, byteorder='little')

    #data
    data = bytes("data", "ASCII")

    #Length of Data
    b_data_size = (data_size).to_bytes(4, byteorder='little')


    header.extend([scot, const_424, scratchpad, title, title_padding,
                  cut_num, align_1, apprx_dur, cue_in, total_length,
                  s_e_dates, s_e_hour, digital, rate_div_100, c_type,
                  compres, eomstrt, opt_params, priorcat, align_2,
                  postcat, opt_params_2, artist_etc, intro_yr, align_3,
                  hour_rec, date_rec, pitch, playlevel, lenvalid,
                  full_f_size, newplaylev, opt_params_3, fact, const_4,
                  b_num_samples, data, b_data_size])


def info(file_name):

    try:
        with open(file_name, 'rb') as wav_file:
            header_stop = 512
            pointer = 4
            total_read = 0
            print("Filename:", file_name)
            while total_read < header_stop:
                print(wav_file.read(pointer))
                print("-----------------------ADDR: ", str(total_read) + "---", end = '')
                total_read += pointer
                print(total_read-1)
    except IOError:
        print("---Info: File {0} cannot be opened.".format(file_name))



def getWavInfo(filename, format_hex = False):
    #Prints out the header in the format
    # Name: Data
    #Tuple is: Name, Size, True/False for Int
    print("Filename:", filename)

    header_data = (['RIFF', 4, False], ['File length - 8', 4, True],
            ['WAVE', 4, False], ['fmt', 4, False], ['FMT chunk size/40??', 4, True],
            ['Format category', 2, True], ['Number of channels', 2, True],
            ['Sampling Rate', 4, True], ['Avg bytes/sec', 4, True],
            ['Data block size', 2, True], ['Format', 2, True],
            ['White space', 24, True], ['scot', 4, False],
            ['424 constant (0xa801)', 4, True], ['Alter (scratchpad)', 1, True],
            ['Attrib (scratchpad)', 1, True], ['Artnum (scratchpad)', 2, True],
            ['Title', 43, False], ['Cut Num', 4, False], ['Padding', 1, True],
            ['Approx duration', 5, False], ['Cue-in (secs)', 2, True],
            ['Cue-in (hundredths)', 2, True], ['Total length (seconds)', 2, True],
            ['Total length (hundredths)', 2, True], ['Start Date', 6, False],
            ['End Date', 6, False], ['Start Hour', 1, True],
            ['End Hour', 1, True], ['Digital', 1, True], ['Sample Rate', 2, True],
            ['Mono/Stereo', 1, False], ['Compress', 1, True],
            ['Eomstrt', 4, True], ['EOM (hundredths from end)', 2, True],
            ['Atrrib2', 4, True], ['Future', 12, True],
            ['catfontcolor', 4, True], ['catcolor', 4, True],
            ['segeompos', 4, True], ['vtstartsecs', 2, True],
            ['vtstarthunds', 2, True], ['priorcat', 3, True],
            ['priorcopy', 4, True], ['priorpadd', 1, True],
            ['postcat', 3, True], ['postcopy', 4, True],
            ['postpadd', 1, True], ['hrcanplay', 21, True],
            ['future', 108, True], ['Artist', 34, False],
            ['Etc/Note', 34, False], ['Intro', 2, False],
            ['End', 1, False], ['Year', 4, False], ['Obsolete2', 1, True],
            ['Hour Recorded', 1, True], ['Date Recorded', 6, False],
            ['Mpegbitrate', 2, True], ['pitch', 2, True], ['playlevel', 2, True],
            ['lenvalid', 1, True], ['filelength', 4, True], ['newplaylev', 2, True],
            ['chopsize', 4, True], ['vteomovr', 4, True], ['desiredlen', 4, True],
            ['triggers[4]', 16, True], ['fillout', 33, True],
            ['fact', 4, False], ['4?????', 4, True],
            ['Number of Audio Samples', 4, True], ['Data', 4, False],
            ['file length - 512', 4, True])

    try:
        with open(filename, 'rb') as wav_file:
            for header in header_data:
                data = wav_file.read(header[1])
                if not format_hex:
                    if header[2]:
                        try:
                            data = int.from_bytes(data, byteorder='little')
                        except TypeError:
                            print("---getWavInfo should've got an Int.---")
                    else:
                        try:
                            data = data.decode("ascii")
                        except UnicodeDecodeError:
                            print("---getWavInfo should've got an ASCII decodeable seq.---")

                print("%-25s: %s" % (header[0], data))

    except IOError:
        print("---getWavInfo couldn't open file {}---".format(filename))

def simpleReWrite(source, dst):

    source = open(source, 'rb')
    dst = open(dst, 'wb')

    for line in source:
        dst.write(line)

    source.close()
    dst.close()
