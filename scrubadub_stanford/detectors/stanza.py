"""
This is a module that provides the same interface as StanfordEntityDetector,
however it uses Stanford's own Python-native Stanza for building pipelines and running annotations.

See https://stanfordnlp.github.io/stanza/ner.html for more details.

Stanza will download the default English language models upon first use. Default location of the download
is `~/stanza_resources` and it is around 210MB in size. If another location is desired, please specify the
path in the environment variable `STANZA_RESOURCES_DIR`.

"""
import re
from typing import List, Dict, Type, Optional

from stanza import Pipeline

from scrubadub.detectors.catalogue import register_detector
from scrubadub.detectors.base import Detector
from scrubadub.filth.base import Filth
from scrubadub.filth.name import NameFilth
from scrubadub.filth.organization import OrganizationFilth
from scrubadub.filth.location import LocationFilth


class StanzaEntityDetector(Detector):
    """Search for people's names, organization's names and locations within text using the stanford 3 class model.

    The three classes of this model can be enabled with the three arguments to the initialiser `enable_person`,
    `enable_organization` and `enable_location`.
    An example of their usage is given below.

    >>> import scrubadub, scrubadub_stanford
    >>> detector = scrubadub_stanford.detectors.StanzaEntityDetector(
    ...     enable_person=False, enable_organization=False, enable_location=True
    ... )
    >>> scrubber = scrubadub.Scrubber(detector_list=[detector])
    >>> scrubber.clean('Jane is visiting London.')
    'Jane is visiting {{LOCATION}}.'
    """
    filth_cls = Filth
    name = "stanford"

    def __init__(self, enable_person: bool = True, enable_organization: bool = True, enable_location: bool = False,
                 ignored_words: List[str] = None,
                 **kwargs):
        """Initialise the ``Detector``.

        :param enable_person: To tag entities that are recognised as person, defaults to `True`.
        :type enable_person: bool
        :param enable_organization: To tag entities that are recognised as organisations, defaults to `True`.
        :type enable_organization: bool
        :param enable_location: To tag entities that are recognised as locations, defaults to `False`.
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
            self.filth_lookup['ORG'] = OrganizationFilth
        if enable_location:
            self.filth_lookup['LOC'] = LocationFilth
        self.ignored_words = ['tennant'] if ignored_words is None else ignored_words
        self._downloaded = False

        super(StanzaEntityDetector, self).__init__(**kwargs)

    def iter_filth(self, text, document_name: Optional[str] = None):
        """Yields discovered filth in the provided ``text``.

        :param text: The dirty text to clean.
        :type text: str
        :param document_name: The name of the document to clean.
        :type document_name: Optional[str]
        :return: An iterator to the discovered :class:`Filth`
        :rtype: Iterator[:class:`Filth`]
        """
        nlp = Pipeline(processors=['tokenize', 'ner'])
        doc = nlp(text)

        grouped_tags = {}  # type: Dict[str, List[str]]
        previous_tag = None

        # List of tuples of text/type for each entity in document
        tags = [(ent.text, ent.type) for ent in doc.ents]
        # Loop over all tagged words and join contiguous words tagged as people
        for tag_text, tag_type in tags:
            if tag_type in self.filth_lookup.keys() and not any(
                    [tag_text.lower().strip() == ignored.lower().strip() for ignored in self.ignored_words]):
                if previous_tag == tag_type:
                    grouped_tags[tag_type][-1] = grouped_tags[tag_type][-1] + ' ' + tag_text
                else:
                    grouped_tags[tag_type] = grouped_tags.get(tag_type, []) + [tag_text]

                previous_tag = tag_type
            else:
                previous_tag = None

        # for each set of tags, de-dupe and convert to regex
        for tag_type, tag_list in grouped_tags.items():
            grouped_tags[tag_type] = [
                r'\b' + re.escape(person).replace(r'\ ', r'\s+') + r'\b'
                for person in set(tag_list)
            ]

        # Now look for these in the original document
        for tag_type, tag_list in grouped_tags.items():
            for tag_regex in tag_list:
                try:
                    pattern = re.compile(tag_regex, re.MULTILINE | re.UNICODE)
                except re.error:
                    print(tag_regex)
                    raise
                found_strings = re.finditer(pattern, text)

                # Iterate over each found string matching this regex and yield some filth
                for instance in found_strings:
                    yield self.filth_lookup[tag_type](
                        beg=instance.start(),
                        end=instance.end(),
                        text=instance.group(),
                        detector_name=self.name,
                        document_name=document_name,
                        locale=self.locale,
                    )

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
