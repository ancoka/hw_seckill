# -*- coding: utf-8 -*-
# !/usr/bin/python

from abc import ABC, abstractmethod

from config import Config


class Browser(ABC):

    @abstractmethod
    def setting(self, config: Config = None, log_path: str = ""):
        pass
