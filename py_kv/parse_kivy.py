from os import rename
from os.path import exists
from os.path import splitext
from os.path import join, isfile, dirname



def writeScottFile(output_name, header, data):
    """
    Writes header and data information to a file.

    Takes in a list of byte objects 'header',
    a list of byte objects 'data' and an 'output_name'
    which is the new scott file. The scott file contains
    the byte objects in header and data.
    """

    with open(output_name, 'wb') as scott_file:
        for item in header:
            scott_file.write(item)

        for item in data:
            scott_file.write(item)


def wavFileType(filename):
    #Given a file, the function will determine
    #whether it is a SCOT WAV file or just a
    #regular WAV file.

    try:
        with open(filename, 'rb') as wav_file:
            wav_file.seek(8)
            is_wav_file = wav_file.read(4)
            if not is_wav_file == bytes('WAVE', 'ASCII'):
                return 'notwav'
            else:
                wav_file.seek(60)
                scot = wav_file.read(4)
                if scot == bytes('scot', 'ASCII'):
                    return 'scottwav'
                else:
                    return 'wav'

    except IOError:
        print("--wavFileType Error--")
        return 'error'



def wavFileHandler(filename, edit_list):
    result = wavFileType(filename)
    if result == 'scottwav':
        editScottWav(filename, edit_list)
    elif result == 'wav':
        wavConvertScott(filename)
    elif result == 'notwav':
        return result
    else:
        return result



def renameScott(filename, new_name, overwrite=False, add_dirname=True):
    final_filename = filename
    try:
        if add_dirname:
            new_name = join(dirname(filename), new_name)
        if not overwrite and isfile(new_name):
            print("---renameScott file {} already exists, not renaming.----".format(new_name))
            return 'owrite'
        else:
            rename(filename, new_name)
            final_filename = new_name
    except IOError:
        print("---renameScott Cannot rename {} to {}.---".format(filename, new_name))

    return final_filename



def editScottWav(filename, edit):
    #Edits the scott file 'filename', optionally re-naming
    #the file.
    addr = {
        "note" : 369, "title" : 72, "artist" : 335, "audio_id" : 115,
        "year" : 406, "end" : 405, "intro" : 403, "eom" : 152,
        "s_date" : 133, "e_date" : 139, "s_hour" : 145, "e_hour": 146
        }

    try:
        with open(filename, 'rb+') as f:
            for name, data in edit:
                f.seek(addr[name])
                if isinstance(data, str):
                    f.write(bytes(data, 'utf-8'))
                else:
                    num_bytes = len(str(abs(data)))
                    f.write((data).to_bytes(num_bytes, byteorder='little'))

    except IOError:
        print("---EditScott cannot open {}. ---".format(filename))



def wavConvertScott(source, id_num ='0000', title_str='Default Title', artist='Default Artist'):
    try:
        header, data = processWav(source, title_str, id_num, artist)
        writeScottFile(source, header, data)
    except IOError:
        print("---wavConvertScott: File {0} cannot be opened.".format(source))



def processWav(filename, title_str, id_num, artist):
    """Gather necessary info from a PCM WAV header.

    """
    #Standard PCM WAV headers are added to a header list.
    #Which are later expanded on to include SCOTT headers.

    import wave
    header = []
    data = []

    #Doesn't work inside ctx manager due to wave.open
    f = wave.open(filename, 'rb')
    num_c = f.getnchannels()
    samp_width = f.getsampwidth()
    samp_rate =  f.getframerate()
    f.close()

    with open(filename, 'rb') as wav_file:
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

        expandHeader(header, num_c, samp_width, samp_rate, i_data_size, f_size, title_str, id_num, artist)

        sound_data = wav_file.read()
        if not len(sound_data) == i_data_size:
            print("Footer information detected.")
        data.append(sound_data)

    return (header, data)

def expandHeader(header, num_c, samp_width, samp_rate, data_size, f_size, title_str, id_num, artist):
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


def info(filename, step=4, stop=512):

    try:
        with open(filename, 'rb') as wav_file:
            print("Filename:", filename)
            total_read = 0
            while total_read < stop:
                print(wav_file.read(step))
                print("-----------------------ADDR: ", str(total_read) + "---", end = '')
                total_read += step
                print(total_read-1)
    except IOError:
        print("---Info: File {0} cannot be opened.".format(filename))


def info_from_file(filename, info_items):
    #info-items is an ordered sequence of
    #keys which correspond to the data you want.

    title_to_addr = {
        'note': (369, 34, 'str'), 'title': (72, 43, 'str'), 'artist': (335, 34, 'str'),
        'audio_id': (115, 4, 'str'), 'year': (406, 4, 'str'), 'end': (405, 1, 'str'),
        'intro': (403, 2, 'str'), 'eom': (152, 6, 'int'), 's_date': (133, 6, 'str'),
        }

    data_to_write = []
    try:
        with open(filename, 'rb') as f:
            for item in info_items:
                f.seek(title_to_addr[item][0])
                if title_to_addr[item][2] == 'str':
                    try:
                        item = f.read(title_to_addr[item][1]).decode('utf-8')
                    except UnicodeDecodeError:
                        item = 'None'
                else:
                    try:
                        raw_bytes = f.read(title_to_addr[item][1])
                        item = int.from_bytes(raw_bytes, byteorder='little')
                    except TypeError:
                        item = 'None'

                data_to_write.append(item)
        return data_to_write
    except IOError:
        print("--- info_from_file: Can't open file", filename)


def printWavInfo(filename, format_hex = False):
    headers = getWavInfo(filename)
    for header in headers:
        name, data = header[0], header[1]
        print("%-25s: %s" % (name, data))


def getWavInfo(filename):
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


    header_list = []
    try:
        with open(filename, 'rb') as wav_file:
            for header in header_data:
                data = wav_file.read(header[1])
                isint = header[2]
                if isint:
                    try:
                        data = int.from_bytes(data, byteorder='little')
                    except TypeError:
                        data = "---getWavInfo should've got an Int.---"
                else:
                    try:
                        data = data.decode("utf-8")
                    except UnicodeDecodeError:
                        data = "---getWavInfo should've got an UTF-8 decodeable seq.---"
                header_list.append((header[0], data))

    except IOError:
        print("---getWavInfo couldn't open file {}---".format(filename))
    return header_list
