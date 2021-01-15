# https://docs.python.org/3/library/wave.html
import wave2 as wave
import sys
import os

import numpy as np

import struct

#calc the rms
#https://www.underbit.com/resources/mpeg/audio/compliance

## usage
def show_usage():
    print("**********************************************")
    print("\nUsage:\npython wav_rms.py <reference wav> <test wav> <int/float>")
    print("\n**********************************************")

def sample_witdh_to_max_value(pcmtype, sampwidth):
    if(pcmtype == 1):
        if(sampwidth == 2):
            return 32768.0
        if(sampwidth == 3):
            return 8388608.0
        if(sampwidth == 4):
            return 2147483648.0
    elif(pcmtype == 3):
        if(sampwidth == 4):
            return 1.0
    print("Format error %d %d" % (pcmtype, sampwidth))

def readdata_to_int(pcmtype, sampwidth, rawdata):
    if(pcmtype == 1):
        if(sampwidth == 2):
            align_data_len = len(rawdata) // 2
            align_data = [0] * int(align_data_len)
            for i in range(align_data_len):
                align_data[i] = int.from_bytes(rawdata[i*2:i*2+2], byteorder='little', signed=True) * 65536
            return align_data
        if(sampwidth == 3):
            align_data_len = len(rawdata) // 3
            align_data = [0] * int(align_data_len)
            for i in range(align_data_len):
                align_data[i] = int.from_bytes(rawdata[i*3:i*3+3], byteorder='little', signed=True) * 256
            return align_data
        if(sampwidth == 4):
            return np.frombuffer(rawdata, np.int32)
    elif(pcmtype == 3):
        if(sampwidth == 4):
            rawdata = np.frombuffer(rawdata, np.float32)
            align_data_len = len(rawdata)
            align_data = [0] * int(align_data_len)
            for i in range(align_data_len):
                align_data[i] = rawdata[i] * 2147483648
            return align_data
    print("Format error %d %d" % (pcmtype, sampwidth))

## process
## 1.all data format to int32
## 2.calc the diff for reference data and decode data
## 3.normalization the diff 
## 4.sum of all sample data
## 5.calc the RMS
##
def wave_rms_calc_with_int(refe_wav_name, test_wav_name):
    diff_rms_sum = 0
    diff_rms_count = 0

    refe_wav = wave.open(refe_wav_name,'r')
    test_wav = wave.open(test_wav_name,'r')

    refe_wav_frames = refe_wav.getnframes()
    refe_wav_rate = refe_wav.getframerate()
    refe_wav_sampwidth = refe_wav.getsampwidth()
    refe_wav_channel = refe_wav.getnchannels()
    refe_wav_pcmtype = refe_wav.getpcmtype()

    #print(refe_wav_frames, refe_wav_rate, refe_wav_sampwidth, refe_wav_channel)

    test_wav_frames = test_wav.getnframes()
    test_wav_rate = test_wav.getframerate()
    test_wav_sampwidth = test_wav.getsampwidth()
    test_wav_channel = test_wav.getnchannels()
    test_wav_pcmtype = test_wav.getpcmtype()

    #print(test_wav_frames, test_wav_rate, test_wav_sampwidth, test_wav_channel)

    if( refe_wav_frames != test_wav_frames ):
        print("Error: Diff frames [%d, %d]" % (refe_wav_frames, test_wav_frames))

    if( refe_wav_rate != refe_wav_rate ):
        print("Error: Diff sample rate [%d, %d]" % (test_wav_rate, test_wav_rate))

    refe_wav_max = sample_witdh_to_max_value(refe_wav_pcmtype, refe_wav_sampwidth)
    test_wav_max = sample_witdh_to_max_value(test_wav_pcmtype, test_wav_sampwidth)

    diff_rms_count = refe_wav_frames * refe_wav_channel
    refe_wav.rewind()
    test_wav.rewind()

    refe_wav_max = sample_witdh_to_max_value(1, 4)

    left_wav_frames = refe_wav_frames
    while(left_wav_frames):
        read_wav_frames = min(left_wav_frames, 1024)

        # numpy rms as int32
        refe_wav_rawdata = refe_wav.readframes(read_wav_frames)
        refe_wav_data = readdata_to_int(refe_wav_pcmtype, refe_wav_sampwidth, refe_wav_rawdata)

        # numpy rms as int32
        test_wav_rawdata = test_wav.readframes(read_wav_frames)
        test_wav_data = readdata_to_int(test_wav_pcmtype, test_wav_sampwidth, test_wav_rawdata)

        for i in range(read_wav_frames * refe_wav_channel):
            # diff 
            diff_wav_data = refe_wav_data[i] - test_wav_data[i]
            # normalization
            diff_wav_data /= refe_wav_max
            # sum
            diff_rms_sum += diff_wav_data*diff_wav_data

        left_wav_frames -= read_wav_frames

    numpy_rms = np.sqrt(diff_rms_sum/diff_rms_count)
    print("%s %s" % (refe_wav_name, test_wav_name))
    print("RMS(Int32):", end="")
    print("%E" % numpy_rms)

def readdata_to_float(pcmtype, sampwidth, rawdata):
    if(pcmtype == 1):
        if(sampwidth == 2):
            return np.frombuffer(rawdata, np.int16).astype(np.float)
        if(sampwidth == 3):
            align_data_len = len(rawdata) // 3
            align_data = [0] * int(align_data_len)
            for i in range(align_data_len):
                align_data[i] = float(int.from_bytes(rawdata[i*3:i*3+3], byteorder='little', signed=True))
            return align_data
        if(sampwidth == 4):
            return np.frombuffer(rawdata, np.int32).astype(np.float)
    elif(pcmtype == 3):
        if(sampwidth == 4):
            return np.frombuffer(rawdata, np.float32).astype(np.float)
    print("Format error %d %d" % (pcmtype, sampwidth))

## process
## 1.all data format to float
## 2.normalization the data 
## 4.calc the diff for normalization reference data and decode data
## 4.sum of all sample data
## 5.calc the RMS
##
def wave_rms_calc_with_float(refe_wav_name, test_wav_name):
    diff_rms_sum = 0
    diff_rms_count = 0

    refe_wav = wave.open(refe_wav_name,'r')
    test_wav = wave.open(test_wav_name,'r')

    refe_wav_frames = refe_wav.getnframes()
    refe_wav_rate = refe_wav.getframerate()
    refe_wav_sampwidth = refe_wav.getsampwidth()
    refe_wav_channel = refe_wav.getnchannels()
    refe_wav_pcmtype = refe_wav.getpcmtype()

    #print(refe_wav_frames, refe_wav_rate, refe_wav_sampwidth, refe_wav_channel)

    test_wav_frames = test_wav.getnframes()
    test_wav_rate = test_wav.getframerate()
    test_wav_sampwidth = test_wav.getsampwidth()
    test_wav_channel = test_wav.getnchannels()
    test_wav_pcmtype = test_wav.getpcmtype()

    #print(test_wav_frames, test_wav_rate, test_wav_sampwidth, test_wav_channel)

    if( refe_wav_frames != test_wav_frames ):
        print("Error: Diff frames [%d, %d]" % (refe_wav_frames, test_wav_frames))

    if( refe_wav_rate != refe_wav_rate ):
        print("Error: Diff sample rate [%d, %d]" % (test_wav_rate, test_wav_rate))

    refe_wav_max = sample_witdh_to_max_value(refe_wav_pcmtype, refe_wav_sampwidth)
    test_wav_max = sample_witdh_to_max_value(test_wav_pcmtype, test_wav_sampwidth)

    refe_wav_data_max = 0
    refe_wav_data_min = 0

    test_wav_data_max = 0
    test_wav_data_min = 0

    refe_wav_max = sample_witdh_to_max_value(refe_wav_pcmtype, refe_wav_sampwidth)
    test_wav_max = sample_witdh_to_max_value(test_wav_pcmtype, test_wav_sampwidth)

    diff_rms_count = refe_wav_frames * refe_wav_channel

    refe_wav.rewind()
    test_wav.rewind()
    left_wav_frames = refe_wav_frames
    while(left_wav_frames):
        read_wav_frames = min(left_wav_frames, 1024)

        # numpy rms as float
        refe_wav_rawdata = refe_wav.readframes(read_wav_frames)
        refe_wav_data = readdata_to_float(refe_wav_pcmtype, refe_wav_sampwidth, refe_wav_rawdata)

        # numpy rms as float
        test_wav_rawdata = test_wav.readframes(read_wav_frames)
        test_wav_data = readdata_to_float(test_wav_pcmtype, test_wav_sampwidth, test_wav_rawdata)

        for i in range(read_wav_frames * refe_wav_channel):
            refe_wav_data_max = max(refe_wav_data[i], refe_wav_data_max)
            refe_wav_data_min = min(refe_wav_data[i], refe_wav_data_min)

            test_wav_data_max = max(test_wav_data[i], test_wav_data_max)
            test_wav_data_min = min(test_wav_data[i], test_wav_data_min)

			# normalization
            # diff 
            diff_wav_data = refe_wav_data[i] / refe_wav_max - test_wav_data[i] / test_wav_max

            # sum
            diff_rms_sum += diff_wav_data*diff_wav_data
            #refe_wav_data[i] = refe_wav_data[i]

        left_wav_frames -= read_wav_frames

    #print( "=============================================" )
    #print( diff_rms_sum, diff_rms_count )
    #print("[min, max]:", end="")
    #print( refe_wav_data_min, refe_wav_data_max)
    #print( refe_wav_data_min / refe_wav_max, refe_wav_data_max / refe_wav_max )
    #print("[min, max]:", end="")
    #print( test_wav_data_min, test_wav_data_max )
    #print( test_wav_data_min / test_wav_max, test_wav_data_max / test_wav_max )

    numpy_rms = np.sqrt(diff_rms_sum/diff_rms_count)
    print("%s %s" % (refe_wav_name, test_wav_name))
    print("RMS(Float):", end="")
    print("%E" % numpy_rms)


if __name__=="__main__":
    num = len(sys.argv)

    if num < 3:
        show_usage()
        sys.exit(1); # error arg

    #reference wav file
    refe_wav_name = sys.argv[1]
    if os.access(refe_wav_name, os.R_OK) != True:
        print("Error: Input file <%s> is not readable" % refe_wav_name)
        show_usage()
        sys.exit(2); # error file

    #test wav file
    test_wav_name = sys.argv[2]
    if os.access(test_wav_name, os.R_OK) != True:
        print("Error: Input file <%s> is not readable" % test_wav_name)
        show_usage()
        sys.exit(2); # error file

    if (num == 4) and (sys.argv[3] == "int") :
        wave_rms_calc_with_int(refe_wav_name, test_wav_name)
    elif (num == 4) and (sys.argv[3] == "float") :
        wave_rms_calc_with_float(refe_wav_name, test_wav_name)
    else:
        wave_rms_calc_with_float(refe_wav_name, test_wav_name)
        wave_rms_calc_with_int(refe_wav_name, test_wav_name)

    sys.exit(0); # success
