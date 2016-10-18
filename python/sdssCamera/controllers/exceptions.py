#!/usr/bin/env python
# encoding: utf-8
#
# exceptions.py
#
# Created by José Sánchez-Gallego on 15 Oct 2016.


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


class HandlerError(Exception):
    pass


class SBIGHandlerError(HandlerError):
    pass