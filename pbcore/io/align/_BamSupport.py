#################################################################################
# Copyright (c) 2011-2015, Pacific Biosciences of California, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of Pacific Biosciences nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE.  THIS SOFTWARE IS PROVIDED BY PACIFIC BIOSCIENCES AND ITS
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL PACIFIC BIOSCIENCES OR
# ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#################################################################################

# Author: David Alexander

import numpy as np

class UnavailableFeature(Exception): pass
class Unimplemented(Exception):      pass
class ReferenceMismatch(Exception):  pass
class IncompatibleFile(Exception):   pass


PULSE_FEATURE_TAGS = { "InsertionQV"    : ("iq", "qv",   np.uint8),
                       "DeletionQV"     : ("dq", "qv",   np.uint8),
                       "DeletionTag"    : ("dt", "base", np.int8 ),
                       "SubstitutionQV" : ("sq", "qv",   np.uint8),
                       "MergeQV"        : ("mq", "qv",   np.uint8),
                       "IPD"            : ("ip", "time", np.uint8),
                       "PulseWidth"     : ("pw", "time", np.uint8) }

COMPLEMENT_MAP = { "A" : "T",
                   "T" : "A",
                   "C" : "G",
                   "G" : "C",
                   "N" : "N",
                   "-" : "-" }

def complementAscii(a):
    return np.array([ord(COMPLEMENT_MAP[chr(b)]) for b in a], dtype=np.int8)

def reverseComplementAscii(a):
    return complementAscii(a)[::-1]


BAM_CMATCH     = 0
BAM_CINS       = 1
BAM_CDEL       = 2
BAM_CREF_SKIP  = 3
BAM_CSOFT_CLIP = 4
BAM_CHARD_CLIP = 5
BAM_CPAD       = 6
BAM_CEQUAL     = 7
BAM_CDIFF      = 8



#
# qId calculation from RG ID string
#
def rgAsInt(rgIdString):
    return np.int32(int(rgIdString, 16))

#
# Kinetics: decode the scheme we are using to encode approximate frame
# counts in 8-bits.
#
def _makeFramepoints():
    B = 2
    t = 6
    T = 2**t

    framepoints = []
    next = 0
    for i in range(256/T):
        grain = B**i
        nextOnes = next + grain * np.arange(0, T)
        next = nextOnes[-1] + grain
        framepoints = framepoints + list(nextOnes)
    return np.array(framepoints, dtype=int)

def _makeLookup(framepoints):
    # (frame -> code) involves some kind of rounding
    # basic round-to-nearest
    frameToCode = np.empty(shape=max(framepoints)+1, dtype=int)
    for i, (fl, fu) in enumerate(zip(framepoints, framepoints[1:])):
        if (fu > fl + 1):
            m = (fl + fu)/2
            for f in xrange(fl, m):
                frameToCode[f] = i
            for f in xrange(m, fu):
                frameToCode[f] = i + 1
        else:
            frameToCode[fl] = i
    # Extra entry for last:
    frameToCode[fu] = i + 1
    return frameToCode, fu

_framepoints = _makeFramepoints()
_frameToCode, _maxFramepoint = _makeLookup(_framepoints)

def framesToCode(nframes):
    nframes = np.minimum(_maxFramepoint, nframes)
    return _frameToCode[nframes]

def codeToFrames(code):
    return _framepoints[code]

def downsampleFrames(nframes):
    return codeToFrames(framesToCode(nframes))
