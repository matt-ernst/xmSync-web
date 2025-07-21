# providers/base.py

from abc import ABC, abstractmethod

class MusicProvider(ABC):
    @abstractmethod
    def add_to_queue(self, song_uri):
        pass

    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def get_name(self):
        pass