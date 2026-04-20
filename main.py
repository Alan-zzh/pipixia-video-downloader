#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
config.ensure_dirs()

from ui.pipixia_app import main

if __name__ == '__main__':
    main()
