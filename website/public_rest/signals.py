#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.dispatch import Signal

sig_email = Signal(providing_args=['kwargs',])
sig_user = Signal(providing_args=['kwargs',])
