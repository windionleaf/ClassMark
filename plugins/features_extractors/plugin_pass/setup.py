#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""""
Created on 4. 3. 2019
Feature extractor plugin for ClassMark.

:author:     Martin Dočekal
:contact:    xdocek09@stud.fit.vubtr.cz
"""

from distutils.core import setup

setup(name='ClassMarkPluginFeatureExtractorPass',
    version='1.0',
    description='Pass feature extractor plugin for ClassMark.',
    author='Martin Dočekal',
    packages=["pass"],
    entry_points={'classmark.plugins.features_extractors': 'pass = pass.pass:Pass'},
    install_requires=[
        'scipy>=1.2'
    ]
)