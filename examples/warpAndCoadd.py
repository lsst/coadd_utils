#!/usr/bin/env python

# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#

from __future__ import with_statement
"""Demonstrate how to create a coadd by warping and adding.
"""
import os
import sys
import time
import traceback

import lsst.pex.logging as pexLog
import lsst.pex.policy as pexPolicy
import lsst.afw.image as afwImage
import lsst.coadd.utils as coaddUtils

SaveDebugImages = False

PolicyPackageName = "coadd_utils"
PolicyDictName = "WarpAndCoaddDictionary.paf"

def warpAndCoadd(coaddPath, exposureListPath, policy):
    """Create a coadd by warping and psf-matching
    
    Inputs:
    - coaddPath: path to desired coadd; ovewritten if it exists
    - exposureListPath: a file containing a list of paths to input exposures;
        blank lines and lines that start with # are ignored
    - policy: policy file; see policy/WarpAndCoaddDictionary.paf
    
    The first exposure in exposureListPath is used as the reference: all other exposures
    are warped to match to it.
    """
    weightPath = os.path.splitext(coaddPath)[0] + "_weight.fits"

    warpPolicy = policy.getPolicy("warpPolicy")
    coaddPolicy = policy.getPolicy("coaddPolicy")

    # process exposures
    coadd = None
    numExposuresInCoadd = 0
    numExposuresFailed = 0
    accumGoodTime = 0
    with file(exposureListPath, "rU") as infile:
        for filePath in infile:
            filePath = filePath.strip()
            if not filePath or filePath.startswith("#"):
                continue
            fileName = os.path.basename(filePath)

            try:
                print >> sys.stderr, "Processing exposure: %s" % (filePath,)
                startTime = time.time()
                exposure = afwImage.ExposureF(filePath)

                if not coadd:
                    print >> sys.stderr, "Create warper and coadd with size and WCS matching the first/reference exposure"
                    warper = coaddUtils.Warp.fromPolicy(warpPolicy)
                    coadd = coaddUtils.Coadd.fromPolicy(
                        bbox = coaddUtils.bboxFromImage(exposure),
                        wcs = exposure.getWcs(),
                        policy = coaddPolicy)
                    print "badPixelMask=", coadd._badPixelMask
                    if SaveDebugImages:
                        exposure.writeFits("warped%s" % (fileName,))
                    
                    print >> sys.stderr, "Add reference exposure to coadd (without warping)"
                    coadd.addExposure(exposure)
                else:
                    print >> sys.stderr, "Warp exposure"
                    warpedExposure = warper.warpExposure(
                        bbox = coadd.getBBox(),
                        wcs = coadd.getWcs(),
                        exposure = exposure)
                    if SaveDebugImages:
                        warpedExposure.writeFits("warped%s" % (fileName,))

                    print >> sys.stderr, "Add warped exposure to coadd"
                    coadd.addExposure(warpedExposure)

                    # ignore time for first exposure since nothing happens to it
                    deltaTime = time.time() - startTime
                    print >> sys.stderr, "Elapsed time for processing exposure: %0.1f sec" % (deltaTime,)
                    accumGoodTime += deltaTime
                numExposuresInCoadd += 1
            except Exception, e:
                print >> sys.stderr, "Exposure %s failed: %s" % (filePath, e)
                traceback.print_exc(file=sys.stderr)
                numExposuresFailed += 1
                continue

    coaddExposure = coadd.getCoadd()
    coaddExposure.writeFits(coaddPath)
    print >> sys.stderr, "Wrote coadd: %s" % (coaddPath,)
    weightMap = coadd.getWeightMap()
    weightMap.writeFits(weightPath)
    print >> sys.stderr, "Wrote weightMap: %s" % (weightPath,)

    print >> sys.stderr, "Coadded %d exposures and failed %d" % (numExposuresInCoadd, numExposuresFailed)
    if numExposuresInCoadd > 1:
        timePerGoodExposure = accumGoodTime / float(numExposuresInCoadd - 1)
        print >> sys.stderr, "Processing speed: %.1f seconds/exposure (ignoring first and failed)" % \
            (timePerGoodExposure,)

if __name__ == "__main__":
    pexLog.Trace.setVerbosity('lsst.coadd', 3)
    helpStr = """Usage: warpAndCoadd.py coaddPath exposureListPath [policy]

where:
- coaddPath is the desired name or path of the output coadd
- exposureListPath is a file containing a list of:
    pathToExposure
  where:
  - pathToExposure is the path to an Exposure
  - the first exposure listed is taken to be the reference exposure,
    which determines the size and WCS of the coadd
  - empty lines and lines that start with # are ignored.
- policy: path to a policy file

The policy dictionary is: policy/%s
""" % (PolicyDictName,)
    if len(sys.argv) not in (3, 4):
        print helpStr
        sys.exit(0)
    
    coaddPath = sys.argv[1]
    if os.path.exists(coaddPath):
        print >> sys.stderr, "Coadd file %s already exists" % (coaddPath,)
        sys.exit(1)
    
    exposureListPath = sys.argv[2]

    if len(sys.argv) > 3:
        policyPath = sys.argv[3]
        policy = pexPolicy.Policy(policyPath)
    else:
        policy = pexPolicy.Policy()

    policyFile = pexPolicy.DefaultPolicyFile(PolicyPackageName, PolicyDictName, "policy")
    defPolicy = pexPolicy.Policy.createPolicy(policyFile, policyFile.getRepositoryPath(), True)
    policy.mergeDefaults(defPolicy.getDictionary())
    
    warpAndCoadd(coaddPath, exposureListPath, policy)
