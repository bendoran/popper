#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Convenience wrapper for running bootstrap directly from source tree."""

from popper.popper import main

if __name__ == '__main__':
    main( config = "conf/test-config.conf", log_file = "/tmp/popper.log" )