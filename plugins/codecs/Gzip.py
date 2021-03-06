# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008-2009 Sebastien Lefevre and other contributors
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
##

##
# ZLIB/GZIP codec.
##

import CodecManager

import zlib

class GZipCodec(CodecManager.Codec):
	def encode(self, template):
		return (zlib.compress(template), 'GZIP data')
	
	def decode(self, data):
		return (zlib.decompress(data), None)

CodecManager.registerCodecClass('gzip', GZipCodec)
