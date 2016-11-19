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
camera.PixelFormat = "Mono8"
camera.gain = 30

def takeImg(expTime, show=True, comment=None):
    # set config
    camera.ExposureTimeAbs = expTime * 1e6

    frame = camera.getFrame()
    frame.announceFrame()
    camera.startCapture()
    frame.queueFrameCapture()
    camera.runFeatureCommand('AcquisitionStart')
    camera.runFeatureCommand('AcquisitionStop')
    frame.waitFrameCapture()

    dtype = numpy.uint8

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
        subprocess.call("ds9 %s -regions load /home/guia/rotCen.reg"%nextImgPath, shell=True)


if __name__ == "__main__":
    """Args:

    exptime (s) mandatory
    """
    nArgs = len(sys.argv)
    assert nArgs == 2
    takeImg(float(nArg[1]))





