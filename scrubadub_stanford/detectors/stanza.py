"""
This is a module that is an alternative to StanfordEntityDetector and does not rely on Java as it uses
Stanford's own Python-native Stanza for building pipelines and running annotations.

See https://stanfordnlp.github.io/stanza/ner.html for more details.

Stanza will download the default English language models upon first use. Default location of the download
is ``~/stanza_resources`` and it is around 210MB in size. If another location is desired, please specify the
path in the environment variable ``STANZA_RESOURCES_DIR``.

"""
import os
from pathlib import Path
from typing import List, Dict, Type, Optional

from stanza import Pipeline

from scrubadub.detectors.catalogue import register_detector
from scrubadub.detectors.base import Detector
from scrubadub.filth.base import Filth
from scrubadub.filth.name import NameFilth
from scrubadub.filth.organization import OrganizationFilth
from scrubadub.filth.location import LocationFilth

from .utils import tag_helper

# Default installation directory for Stanza download (210MB)
HOME_DIR = str(Path.home())
DEFAULT_STANZA_DIR = os.getenv(
    'STANZA_RESOURCES_DIR',
    os.path.join(HOME_DIR, 'stanza_resources')
)


class StanzaEntityDetector(Detector):
    """Search for people's names, organization's names and locations within text using the stanford 3 class model.

    The three classes of this model can be enabled with the three arguments to the initialiser ``enable_person``,
    ``enable_organization`` and `enable_location`.
    An example of their usage is given below.

    >>> import scrubadub
    >>> from scrubadub_stanford.detectors import StanzaEntityDetector
    >>>
    >>> detector = StanzaEntityDetector(
    ...     enable_person=True, enable_organization=True, enable_location=False
    ... )
    >>> scrubber = scrubadub.Scrubber(detector_list=[detector])
    >>> scrubber.clean('Jane has an appointment at the National Hospital of Neurology and Neurosurgery today.')
    '{{NAME}} has an appointment at {{ORGANIZATION}} today.'
    """
    filth_cls = Filth
    name = "stanza"

    def __init__(self, enable_person: bool = True, enable_organization: bool = True, enable_location: bool = False,
                 ignored_words: List[str] = None,
                 **kwargs):
        """Initialise the ``Detector``.

        :param enable_person: To tag entities that are recognised as person, defaults to ``True``.
        :type enable_person: bool
        :param enable_organization: To tag entities that are recognised as organisations, defaults to ``True``.
        :type enable_organization: bool
        :param enable_location: To tag entities that are recognised as locations, defaults to ``False``.
        :type enable_location: bool
        :param ignored_words: A list of words that will be ignored by the NER tagging. Defaults to ``['tennant']``.
        :type ignored_words: List[str]
        :param name: Overrides the default name of the :class:``Detector``
        :type name: str, optional
        :param locale: The locale of the documents in the format: 2 letter lower-case language code followed by an
                       underscore and the two letter upper-case country code, eg "en_GB" or "de_CH".
        :type locale: str, optional
        """
        self.filth_lookup = {}  # type: Dict[str, Type[Filth]]
        if enable_person:
            self.filth_lookup['PERSON'] = NameFilth
        if enable_organization:
            self.filth_lookup['ORG'] = OrganizationFilth
        if enable_location:
            self.filth_lookup['LOC'] = LocationFilth
        self.ignored_words = ['tennant'] if ignored_words is None else ignored_words
        self._downloaded = False

        super(StanzaEntityDetector, self).__init__(**kwargs)

    @staticmethod
    def _check_downloaded(directory: str = DEFAULT_STANZA_DIR) -> bool:
        """Check for a downloaded Stanza's resources.

        :param directory: The directory where Stanza's models will have been downloaded to, default is
                          ``stanza_resources`` in the home directory, else specified by the environment variable
                          ``STANZA_RESOURCES_DIR``.
        :type directory: str
        :return: ``True`` if the directory exists and is not empty.
        :rtype: bool
        """
        directory = os.path.expanduser(directory)
        if os.path.exists(directory) and 'en' in os.listdir(directory):
            return True
        return False

    def iter_filth(self, text: str, document_name: Optional[str] = None):
        """Yields discovered filth in the provided ``text``.

        :param text: The dirty text to clean.
        :type text: str
        :param document_name: The name of the document to clean.
        :type document_name: Optional[str]
        :return: An iterator to the discovered :class:`Filth`
        :rtype: Iterator[:class:`Filth`]
        """
        processors = ['tokenize', 'ner']
        if not self._check_downloaded():
            pipeline = Pipeline(processors=processors)
        pipeline = Pipeline(processors=processors, download_method=None)
        doc = pipeline(text)
        # List of tuples of text/type for each entity in document
        tags = [(ent.text, ent.type) for ent in doc.ents]
        return tag_helper(text=text, tags=tags, filth_lookup=self.filth_lookup, ignored_words=self.ignored_words,
                          name=self.name, locale=self.locale, document_name=document_name)

    @classmethod
    def supported_locale(cls, locale: str) -> bool:
        """Returns true if this ``Detector`` supports the given locale.

        :param locale: The locale of the documents in the format: 2 letter lower-case language code followed by an
                       underscore and the two letter upper-case country code, eg "en_GB" or "de_CH".
        :type locale: str
        :return: ``True`` if the locale is supported, otherwise ``False``
        :rtype: bool
        """
        language, region = cls.locale_split(locale)
        return language in ['en']


register_detector(StanzaEntityDetector)

__all__ = ["StanzaEntityDetector"]
