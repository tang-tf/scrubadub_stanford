"""
Helper function for iterating through annotated list of entities done by Stanford NER models"
"""
from typing import Dict, Type, List, Tuple, Optional
import re

from scrubadub.filth.base import Filth


def tag_helper(text: str, tags: List[Tuple[str, str]], filth_lookup: Dict[str, Type[Filth]], ignored_words: List[str],
               name: str, locale: str, document_name: Optional[str] = None):
    """
    Helper function to iterate through a list of tuples that contain the string and its entity tag to check if for
    matching filth or if the string should be ignored and returns what is expected from Detector base class's iter_filth

    :param text: The text of the annotated Document for reverse search of index
    :type text: str
    :param tags: The list of tuples of annotated entities
    :type tags: List[Tuple[str, str]]
    :param filth_lookup: The type of Filth identified by its annotation
    :type filth_lookup: Dict[str, Type[Filth]]
    :param ignored_words: List of words to ignore, set in the Stanford-type Detector's init params
    :type ignored_words: List[str]
    :param name: Name of the Detector class
    :type name: str
    :param locale: Locale of the Detector's annotation model
    :type locale: str
    :param document_name: Name of the document if specified
    :type document_name: Optional[str]
    :return: Iterator of discovered Filth
    :rtype: Generator[Type[Filth]]
    """
    grouped_tags = {}  # type: Dict[str, List[str]]
    previous_tag = None
    for tag_text, tag_type in tags:
        if tag_type in filth_lookup.keys() and not any(
                [tag_text.lower().strip() == ignored.lower().strip() for ignored in ignored_words]):
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
                yield filth_lookup[tag_type](
                    beg=instance.start(),
                    end=instance.end(),
                    text=instance.group(),
                    detector_name=name,
                    document_name=document_name,
                    locale=locale,
                )
