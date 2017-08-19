#### PATTERN #######################################################################################

# Authors: Tom De Smedt <tom@organisms.be>, Walter Daelemans <walter.daelemans@ua.ac.be>
# License: BSD License, see LICENSE.txt

#### BSD LICENSE ###################################################################################

# Copyright (c) 2010 University of Antwerp, Belgium
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     * Neither the name of Pattern nor the names of its
#       contributors may be used to endorse or promote products
#       derived from this software without specific prior written
#       permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#   BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#   CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#   ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#   POSSIBILITY OF SUCH DAMAGE.
#
# CLiPS Computational Linguistics Group, University of Antwerp, Belgium
# http://www.clips.ua.ac.be/pages/pattern

from __future__ import unicode_literals

### CREDITS ########################################################################################

__author__    = "Tom De Smedt"
__credits__   = "Tom De Smedt, Walter Daelemans"
__version__   = "2.6"
__copyright__ = "Copyright (c) 2010 University of Antwerp (BE)"
__license__   = "BSD"

####################################################################################################

import os

# Shortcuts to pattern.en, pattern.es, ...
# (instead of pattern.text.en, pattern.text.es, ...)
try:
    __path__.append(os.path.join(__path__[0], "text"))
except:
    pass
