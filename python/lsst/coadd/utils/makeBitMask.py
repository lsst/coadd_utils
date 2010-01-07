import lsst.afw.image as afwImage

__all__ = ["makeBitMask"]

def makeBitMask(maskPlaneNameList, doInvert=False):
    """Generate a bit mask consisting of ORed together Mask bit planes
    
    Inputs:
    - maskPlaneNameList: list of mask plane names
    - doInvert: if True then invert the result
    
    @return a bit mask consisting of the named bit planes ORed together (with the result possibly inverted)
    """
    bitMask = 0
    for maskPlaneName in maskPlaneNameList:
        bitMask |= afwImage.MaskU.getPlaneBitMask(maskPlaneName)
    if doInvert:
        bitMask = (2**afwImage.MaskU_getNumPlanesMax() - 1) - bitMask
    return bitMask
