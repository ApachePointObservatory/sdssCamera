# script to take an exposure with an AlliedVision manga and save it sequentially to the directory:
# ~/mantaImg/
import sys
import os
import glob
import subprocess

import numpy
from astropy.io import fits
from astropy.time import Time

import pymba

IMG_DIR = os.path.join(os.path.expanduser("~"), "mantaImg")
BASE_NAME = "manga"
EXT = "fits"
MANTA_ID = "DEV_000F314D1D98"

pixelFormats = ["Mono8", "Mono12"]
gainRange = [0, 40]

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

def writeFits(imgData, filename, expTime, comment=None):
    hdu = fits.PrimaryHDU(imgData)
    hdulist = fits.HDUList([hdu])
    prihdr = hdulist[0].header
    prihdr["obstime"] = Time.now().isot, "UNIX time of exposure"
    prihdr["exptime"] = expTime
    if comment is not None:
        prihdr['comment'] = comment
    hdulist.writeto(filename)
    hdulist.close()

def getNextImgPath():
    allImgs = sorted(glob.glob(os.path.join(IMG_DIR, "*.fits")))
    if not allImgs:
        nextImgNum = 1
    else:
        lastImg = os.path.split(allImgs[-1])[-1] # just get file name, not full path
        nextImgNum = int(lastImg.strip("."+EXT).strip(BASE_NAME)) + 1

    zeroPadNum = ("%i"%nextImgNum).zfill(6)
    nextImgName = "%s%s.%s"%(BASE_NAME, zeroPadNum, EXT)
    # send full path back
    return os.path.join(IMG_DIR, nextImgName)

vimba = pymba.Vimba()
vimba.startup()
system = vimba.getSystem()
system.runFeatureCommand("GeVDiscoveryAllOnce")
camera = vimba.getCamera(MANTA_ID)
camera.openCamera()
camera.AcquisionMode = "SingleFrame"

def takeImg(expTime, gain=0, pixelFormat="Mono12", comment=None, show=True):
    # set config
    camera.ExposureTimeAbs = expTime * 1e6
    camera.PixelFormat = pixelFormat
    camera.gain = gain

    frame = camera.getFrame()
    frame.announceFrame()
    camera.startCapture()
    frame.queueFrameCapture()
    camera.runFeatureCommand('AcquisitionStart')
    camera.runFeatureCommand('AcquisitionStop')
    frame.waitFrameCapture()

    if pixelFormat == "Mono8":
        dtype = numpy.uint8
    else:
        dtype = numpy.uint16

    imgData = numpy.ndarray(buffer = frame.getBufferByteData(),
                                   dtype = dtype,
                                   shape = (frame.height,
                                            frame.width)
                                   )
    nextImgPath = getNextImgPath()
    print("writing: %s"%nextImgPath)
    writeFits(imgData, nextImgPath, expTime, comment=comment)
    # clean up after capture
    camera.endCapture()
    camera.revokeAllFrames()
    if show:
        subprocess.call("ds9 %s"%nextImgPath, shell=True)


if __name__ == "__main__":
    """Args:

    exptime (s) mandatory
    gain 1-40 (optional) [default 1]
    pixelFormat [Mono8, Mono12] [default Mono12]
    """
    nArgs = len(sys.argv)
    gain = 1
    pixelFormat = "Mono12"
    if not nArgs > 1:
        raise RuntimeError("Must specify exposure time")
    try:
        expTime = float(sys.argv[1])
    except:
        raise RuntimeError("couldn't parse %s as float for exposure time"%sys.argv[1])
    if nArgs > 2:
        try:
            gain = float(sys.argv[2])
            assert gainRange[0] <= gain <= gainRange[1]
        except:
            raise RuntimeError("couldn't parse gain %s as a float between %i and %i"%(sys.argv[2], gainRange[0], gainRange[1]))
    if nArgs > 3:
        try:
            pixelFormat = str(sys.argv[3]).capitalize()
            assert pixelFormat in pixelFormats
        except:
            raise RuntimeError("couldn't parse pixel format as one of %s"%str(pixelFormats))





