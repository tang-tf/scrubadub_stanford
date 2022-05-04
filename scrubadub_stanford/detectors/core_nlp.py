"""
This is a module that provides the same interface as StanfordEntityDetector,
however it uses Stanford's own Stanza API to interface with the CoreNLP Java Server
instead of using NLTK's interface.

See https://stanfordnlp.github.io/CoreNLP/ for more details.
This detector requires Java Runtime Environment 8+ and the Stanford CoreNLP installation is about 510MB.
The default installation location is ``~/stanza_corenlp``, but a different location can be specified using
environment variable ``CORENLP_HOME``.
"""
import os
from pathlib import Path
from typing import List, Dict, Type, Optional

from stanza import install_corenlp
from stanza.server import CoreNLPClient

from scrubadub.detectors.catalogue import register_detector
from scrubadub.detectors.base import Detector
from scrubadub.filth.base import Filth
from scrubadub.filth.name import NameFilth
from scrubadub.filth.organization import OrganizationFilth
from scrubadub.filth.location import LocationFilth

from .utils import tag_helper

# Default installation directory for CoreNLP download (500MB)
HOME_DIR = str(Path.home())
DEFAULT_CORENLP_DIR = os.getenv(
    'CORENLP_HOME',
    os.path.join(HOME_DIR, 'stanza_corenlp')
)


class CoreNlpEntityDetector(Detector):
    """Search for people's names, organization's names and locations within text using the stanford 3 class model.

    The three classes of this model can be enabled with the three arguments to the initialiser ``enable_person``,
    ``enable_organization`` and ``enable_location``.
    An example of their usage is given below.

    >>> from scrubadub import Scrubber
    >>> from scrubadub_stanford.detectors import CoreNlpEntityDetector
    >>>
    >>> detector = CoreNlpEntityDetector(
    ...     enable_person=True, enable_organization=True, enable_location=False
    ... )
    >>> scrubber = Scrubber(detector_list=[detector])
    >>> scrubber.clean('Jane has an appointment at the National Hospital of Neurology and Neurosurgery today.')
    '{{NAME}} has an appointment at the {{ORGANIZATION}} and Neurosurgery today.'
    """
    filth_cls = Filth
    name = "corenlp"

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
        :param ignored_words: A list of words that will be ignored by the NER tagging. Defaults to `['tennant']`.
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
            self.filth_lookup['ORGANIZATION'] = OrganizationFilth
        if enable_location:
            self.filth_lookup['LOCATION'] = LocationFilth
        self.ignored_words = ['tennant'] if ignored_words is None else ignored_words

        super(CoreNlpEntityDetector, self).__init__(**kwargs)

    @staticmethod
    def _check_downloaded(directory: str = DEFAULT_CORENLP_DIR) -> bool:
        """Check for a downloaded Stanford CoreNLP.

        :param directory: The directory where CoreNLP will be unzipped and installed to, default is ``stanza_corenlp``
                          in the home directory, else specified by the environment variable ``CORENLP_HOME``.
        :type directory: str
        :return: ``True`` if the directory exists and is not empty.
        :rtype: bool
        """
        directory = os.path.expanduser(directory)
        if os.path.exists(directory) and len(os.listdir(directory)) > 0:
            return True
        return False

    @staticmethod
    def _download(directory: str = DEFAULT_CORENLP_DIR) -> None:
        """Download and install CoreNLP to the specified directory.

        :param directory: The directory where CoreNLP will be unzipped and installed to, default is ``stanza_corenlp``
                          in the home directory, else specified by the environment variable ``CORENLP_HOME``.
        :type directory: str
        """
        install_corenlp(directory)

    def iter_filth(self, text, document_name: Optional[str] = None):
        """Yields discovered filth in the provided ``text``.

        :param text: The dirty text to clean.
        :type text: str
        :param document_name: The name of the document to clean.
        :type document_name: Optional[str]
        :return: An iterator to the discovered :class:`Filth`
        :rtype: Iterator[:class:`Filth`]
        """

        if not self._check_downloaded():
            self._download()

        with CoreNLPClient(be_quiet=True) as client:
            annotation = client.annotate(text)

        # List of tuples of token/NER tag for each token of each annotated sentence:
        tags = [(token.value, token.ner) for sentence in annotation.sentence for token in sentence.token]
        # Loop over all tagged words and join contiguous words tagged as people
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


register_detector(CoreNlpEntityDetector)

__all__ = ["CoreNlpEntityDetector"]
