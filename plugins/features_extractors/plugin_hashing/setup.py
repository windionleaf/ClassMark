#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
""""
Created on 4. 3. 2019
Feature extractor plugin for ClassMark.

:author:     Martin Dočekal
:contact:    xdocek09@stud.fit.vubtr.cz
"""

from distutils.core import setup

setup(name='ClassMarkPluginFeatureExtractorHashing',
    version='1.0dev',
    description='Hashing feature extractor plugin for ClassMark.',
    author='Martin Dočekal',
    entry_points={'classmark.plugins.features_extractors': 'hashing = hashing:Hashing'},
    install_requires=[
        'scikit_learn==0.21.1'
    ]
    
)