import numpy
import scipy.io.wavfile
import scipy.signal
from scipy import fftpack
import sys
from PIL import Image
from PIL import ImageEnhance
import subprocess
import argparse
import librosa
from os.path import dirname, join
import os
from scipy.signal import butter, sosfilt, sosfreqz
import imageio
import math

class APT_signal(object):
    # The audio should get resampled to 20.8 kHz if not there natively
    SAMPLE_RATE = 20800

    def __init__ (self, wavIN):
        f = open(join(dirname(__file__), "test.txt"), "w")
        f.write("Loading audio file...")
        f.close()
        print("Loading audio file...")
        try:
            data, rate = librosa.core.load(wavIN, sr=self.SAMPLE_RATE, mono=True, duration=450)
            if len(data)/rate == 450:
                data2, rate2 = librosa.core.load(wavIN, sr=self.SAMPLE_RATE, mono=True, offset=450)
                data = numpy.concatenate((data, data2))
            librosa.output.write_wav(wavIN[:-4] + "_converted.wav", data, rate)
            (rate, self.signal) = scipy.io.wavfile.read(wavIN[:-4] + "_converted.wav")
            f = open(join(dirname(__file__), "test.txt"), "w")
            f.write("Done resample and remixing.")
            f.close()
            print("Done resample and remixing.\n")
        except:
            f = open(join(dirname(__file__), "test.txt"), "w")
            f.write("ERROR! Failed to open input file.")
            f.close()
            print("ERROR! Failed to open input file.")
            sys.exit("Stopping")

    def decode(self, outfile=None, shrp=False, cmbn=False, contr=False, filter=False, a=False, b=False):
        #Bandpass filter
        if filter == True:
            def butter_bandpass_filter(data, lowcut, highcut, fs, order=6):

                def butter_bandpass(lowcut, highcut, fs, order=6):
                    nyq = 0.5 * fs
                    low = lowcut / nyq
                    high = highcut / nyq
                    sos = butter(order, low, analog=False, btype='lowpass', output='sos')
                    return sos

                sos = butter_bandpass(lowcut, highcut, fs, order=order)
                y = sosfilt(sos, data)
                return y

            lowcut = 2300
            highcut = 2500
            fs = 20800
            f = open(join(dirname(__file__), "test.txt"), "w")
            f.write("Applying bandpass filter")
            f.close()
            print("Applying bandpass filter")
            signalButter = butter_bandpass_filter(self.signal, lowcut, highcut, fs)
            print("Done.\n")

        # Take the Hilbert transform
        f = open(join(dirname(__file__), "test.txt"), "w")
        f.write("Taking Hilbert transform...")
        f.close()
        print("Taking Hilbert transform...")
        try:
            splitNum = math.ceil((len(self.signal)/self.SAMPLE_RATE)/60)
            print("splitting in {} pieces".format(splitNum))
            splitLen = len(self.signal) - (len(self.signal)%splitNum)
            if splitLen < len(self.signal):
                self.signal = self.signal[:int(-(len(self.signal)-splitLen))].copy()
            split = numpy.split(self.signal, splitNum)
            signalHilbert = numpy.array([])

            i = 1
            for array in split:
                Siglenght = scipy.fftpack.next_fast_len(int(len(array)))
                padding = numpy.zeros((int(Siglenght)) - len(array))
                toHilbert = numpy.hstack((array, padding))
                temp = scipy.signal.hilbert(array)
                temp = temp[0:len(array)]
                signalHilbert = numpy.concatenate((signalHilbert, temp))
                print("transformed {}/{}".format(i, splitNum))
                i += 1
            print("Done.\n")
        except Exception as e:
            f = open(join(dirname(__file__), "test.txt"), "w")
            print(e)
            f.write("ERROR! Probably ran out of ram. Close all other open apps and try again")
            f.close()
            print("ERROR! Probably ran out of ram. Close all other open apps and try again")
            sys.exit("Stopping")

        # Median filter
        f = open(join(dirname(__file__), "test.txt"), "w")
        f.write("Taking median filter...")
        f.close()
        print("Taking median filter...")
        signalMed = scipy.signal.medfilt(numpy.abs(signalHilbert), 5)
        print("Done.\n")

        # Calculate how many elements off our reshaped array will be
        f = open(join(dirname(__file__), "test.txt"), "w")
        f.write("Calculating necessary truncation...")
        f.close()
        print("Calculating necessary truncation...")
        elementDiff = len(signalMed) - ((len(signalMed) // 5)*5)
        print("Done.\n")

        # Truncate the filtered signal to that number of elements
        f = open(join(dirname(__file__), "test.txt"), "w")
        f.write("Truncating signal...")
        f.close()
        print("Truncating signal...")
        signalMedTrunc = signalMed[:len(signalMed)-elementDiff]
        print("Done.\n")

        # Reshape the truncated filtered signal to have five columns
        f = open(join(dirname(__file__), "test.txt"), "w")
        f.write("Reshaping signal...")
        f.close()
        print("Reshaping signal...")
        signalReshaped = signalMedTrunc.reshape((len(signalMed) // 5, 5))
        print("Done.\n")

        # Digitize the reshaped signal
        f = open(join(dirname(__file__), "test.txt"), "w")
        f.write("Digitizing signal...")
        f.close()
        print("Digitizing signal...")
        signalDigitized = self._digitize(signalReshaped[:, 2])
        print("Done.\n")

        # Sync the scanlines
        f = open(join(dirname(__file__), "test.txt"), "w")
        f.write("Synchronizing scanlines... (this might take a while)")
        f.close()
        print("Synchronizing scanlines...")
        try:
            matrix = self._reshape(signalDigitized)
        except:
            f = open(join(dirname(__file__), "test.txt"), "w")
            f.write("ERROR! dont know what when wrong tbh")
            f.close()
            sys.exit("Error")
        print("Done.\n")

        # Create image with data
        f = open(join(dirname(__file__), "test.txt"), "w")
        f.write("Forming image...")
        f.close()
        print("Forming image...")
        image = Image.fromarray(matrix)
        if not outfile is None:
            image.save(outfile + "_original.png")
            outfile1 = (outfile + "_original.png")
        print("Done.\n")

        #Combine channels
        if cmbn == True:
            f = open(join(dirname(__file__), "test.txt"), "w")
            f.write("Combining the channels")
            f.close()
            print("Combining the channels")
            img = imageio.imread(outfile1)
            height, width = img.shape
            width_cutoff = width // 2
            s1 = img[:, :width_cutoff]
            s2 = img[:, width_cutoff:]
            imageio.imsave(outfile + "_a.png", s1)
            imageio.imsave(outfile + "_b.png", s2)
            imR = Image.open(outfile + "_a.png")
            imGB = Image.open(outfile + "_b.png")
            imC = Image.merge('RGB', (imR, imGB, imGB))
            imC.save(outfile + "_combined.png")
            outfile2 = (outfile + "_combined.png")
        if a != True:
            os.remove(outfile + "_a.png")
        if b != True:
            os.remove(outfile + "_b.png")
            print("Done.\n")

        #Sharpen image
        if shrp is float(1.0):
            
            print("Sharpening image...")
            sharpen = Image.open(outfile1)
            sharpen.load()
            enh1 = ImageEnhance.Sharpness(sharpen)
            Enhanced = enh1.enhance(shrp).save(outfile + "_s.png")
            print("Done.\n")

        #Contrast adjustment
        if contr is float(1.0):
            print("Contrast adjustment")
            add = ""
            if shrp is float(1.0):
                contrast = Image.open(outfile + "_s.png")
                add = "_s"
            else:
                contrast = Image.opem(outfile1)
            contrast.load()
            enh2 = ImageEnhance.Contrast(contrast)
            Contrasted = enh2.enhance(contr).save(outfile + add +"_Contrast.png")
            os.remove(outfile + "_s.png")
            print("Done.\n")

        return matrix

    def _digitize(self, signal, plow=0.5, phigh=99.5):
        # Calculate low and high reach of signal
        (low, high) = numpy.percentile(signal, (plow, phigh))
        delta = high - low

        # Normalize the signal to px luminance values, discretize
        data = numpy.round(255 * (signal - low) / delta)
        data[data < 0] = 0
        data[data > 255] = 255
        return data.astype(numpy.uint8)

    def _reshape(self, signal):
        # We are searching for a sync frame, which will appear as seven pulses
        # with some black pixels
        syncA = [0, 128, 255, 128]*7 + [0]*7

        # Track maximum correlations found: (index, val)
        peaks = [(0, 0)]

        # There is a minimum distance between peaks, probably more than 2000
        mindistance = 2000

        # Downshift values to get meaningful correlation
        signalshifted = [x-128 for x in signal]
        syncA = [x-128 for x in syncA]
        for i in range(len(signal)-len(syncA)):
            corr = numpy.dot(syncA, signalshifted[i:i+len(syncA)])

            # If previous peak is too far, we keep it but add this value as new
            if i - peaks[-1][0] > mindistance:
                peaks.append((i, corr))
            elif corr > peaks[-1][1]:
                peaks[-1] = (i, corr)

        # Create image matrix, starting each line at the peaks
        matrix = []
        for i in range(len(peaks) - 1):
            matrix.append(signal[peaks[i][0] : peaks[i][0] + 2080])

        return numpy.array(matrix)


def main(infile, outfile):
    outfile += "/{}".format(infile.split("/")[-1][:-4])
    print(outfile)
    infile = join(dirname(__file__), infile)
    apt = APT_signal(infile)
    apt.decode(outfile=outfile, shrp=1.0, cmbn=True, contr=1.0, filter=True, a=True, b=True)
    os.remove(infile)
    os.remove(infile[:-4] + "_converted.wav")

    f = open(join(dirname(__file__), "test.txt"), "w")
    f.write("DONE!")
    f.close()