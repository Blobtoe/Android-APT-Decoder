import numpy
import scipy.io.wavfile
import scipy.signal
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

class APT_signal(object):
    # The audio should get resampled to 20.8 kHz if not there natively
    SAMPLE_RATE = 20800

    def __init__ (self, wavIN):
        print("Loading audio file...")
        data, rate = librosa.core.load(wavIN, sr=self.SAMPLE_RATE, mono=True, duration=450)
        if len(data)/rate == 450:
            data2, rate2 = librosa.core.load(wavIN, sr=self.SAMPLE_RATE, mono=True, offset=450)
            data = numpy.concatenate((data, data2))
        librosa.output.write_wav(wavIN[:-4] + "_converted.wav", data, rate)
        (rate, self.signal) = scipy.io.wavfile.read(wavIN[:-4] + "_converted.wav")
        print("Done resample and remixing.\n")

    def decode(self, outfile=None, shrp=1.0, cmbn=None, contr=1.0, filter=None):
        #Bandpass filter
        if not filter is None:
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
            print("Applying bandpass filter")
            signalButter = butter_bandpass_filter(self.signal, lowcut, highcut, fs)
            print("Done.\n")

        # Take the Hilbert transform
        print("Taking Hilbert transform...")
        splitNum = 10
        splitLen = len(self.signal) - (len(self.signal)%splitNum)
        if splitLen < len(self.signal):
            self.signal = self.signal[:int(-(len(self.signal)-splitLen))].copy()
        split = numpy.split(self.signal, splitNum)
        signalHilbert = numpy.array([])
        i = 1
        for array in split:
            temp = scipy.signal.hilbert(array)
            signalHilbert = numpy.concatenate((signalHilbert, temp))
            print("transformed {}/{}".format(i, splitNum))
            i += 1
        print("Done.\n")

        # Median filter
        print("Taking median filter...")
        signalMed = scipy.signal.medfilt(numpy.abs(signalHilbert), 5)
        print("Done.\n")

        # Calculate how many elements off our reshaped array will be
        print("Calculating necessary truncation...")
        elementDiff = len(signalMed) - ((len(signalMed) // 5)*5)
        print("Done.\n")

        # Truncate the filtered signal to that number of elements
        print("Truncating signal...")
        signalMedTrunc = signalMed[:len(signalMed)-elementDiff]
        print("Done.\n")

        # Reshape the truncated filtered signal to have five columns
        print("Reshaping signal...")
        signalReshaped = signalMedTrunc.reshape((len(signalMed) // 5, 5))
        print("Done.\n")

        # Digitize the reshaped signal
        print("Digitizing signal...")
        signalDigitized = self._digitize(signalReshaped[:, 2])
        print("Done.\n")

        # Sync the scanlines
        print("Synchronizing scanlines...")
        matrix = self._reshape(signalDigitized)
        print("Done.\n")

        # Create image with data
        print("Forming image...")
        image = Image.fromarray(matrix)
        if not outfile is None:
            image.save(outfile + "_original.png")
            outfile1 = (outfile + "_original.png")
        print("Done.\n")

        #Combine channels
        if not cmbn is None:
            print("Combining the channels")
            img = imageio.imread(outfile1)
            height, width = img.shape
            width_cutoff = width // 2
            s1 = img[:, :width_cutoff]
            s2 = img[:, width_cutoff:]
            imageio.imsave(outfile + "_puoli1.png", s1)
            imageio.imsave(outfile + "_puoli2.png", s2)
            imR = Image.open(outfile + "_puoli1.png")
            imGB = Image.open(outfile + "_puoli2.png")
            imC = Image.merge('RGB', (imR, imGB, imGB))
            imC.save(outfile + "_combined.png")
            outfile2 = (outfile + "_combined.png")
            #subprocess.call(["rm", outfile + "_puoli1.png"])
            #subprocess.call(["rm", outfile + "_puoli2.png"])
            print("Done.\n")

        #Sharpen image
        if not shrp is float(1.0):
            print("Sharpening image...")
            if not cmbn is None:
                sharpen = Image.open(outfile2)
            else:
                sharpen = Image.open(outfile1)
            sharpen.load()
            enh1 = ImageEnhance.Sharpness(sharpen)
            Enhanced = enh1.enhance(shrp).save(outfile + "_s.png")
            print("Done.\n")

        #Contrast adjustment
        if not contr is float(1.0):
            print("Contrast adjustment")
            if not shrp is float(1.0):
                contrast = Image.open(outfile + "_s.png")
            elif not cmbn is None:
                contrast = Image.open(outfile2)
            else:
                contrast = Image.opem(outfile1)
            contrast.load()
            enh2 = ImageEnhance.Contrast(contrast)
            Contrasted = enh2.enhance(contr).save(outfile + "_Contrast.png")
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
    infile = join(dirname(__file__), infile)
    print(infile)
    #outfile = join(dirname(__file__), "test.png")
    #infile = "/storage/emulated/0/audio.wav"
    #outfile = "/storage/emulated/0/test.png"
    apt = APT_signal(infile)
    apt.decode(outfile, 1.0, 1.0, 1.0, 1)
    os.remove(infile)
    os.remove(infile[:-4] + "_converted.wav")