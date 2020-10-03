from typing import Type

from .OggTagger import OggTagger
from .FLACTagger import FLACTagger
from .ID3Tagger import ID3Tagger
from .ASFTagger import ASFTagger
from .MP4Tagger import MP4Tagger
from .APEv2Tagger import APEv2Tagger
from .BaseTagger import BaseTagger

taggers = [OggTagger, FLACTagger, ID3Tagger, ASFTagger, MP4Tagger, APEv2Tagger]


def tagger_for_type(format_type) -> Type[BaseTagger]:
    for tagger in taggers:
        if format_type in tagger.format_types:
            return tagger


def tagger_by_name(name: str) -> Type[BaseTagger]:
    for tagger in taggers:
        if tagger.__name__ == name:
            return tagger
