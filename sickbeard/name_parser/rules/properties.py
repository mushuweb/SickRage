#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Properties: This section contains additional properties to be guessed by guessit."""
import re
from string import upper

import babelfish
from guessit.rules.common import dash, alt_dash
from guessit.rules.common.validators import seps, seps_surround
from rebulk.processors import POST_PROCESS
from rebulk.rebulk import Rebulk
from rebulk.rules import Rule, RemoveMatch


def blacklist():
    """Blacklisted patterns.

    All blacklisted patterns should use `other` property and be private.
    :return:
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name='other', private=True)
    rebulk.regex('DownRev', 'small-size')

    return rebulk


def format_():
    """Format property.

    :return:
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name='format')

    # https://github.com/guessit-io/guessit/issues/307
    rebulk.regex('HDTV-?Mux', value='HDTV')
    rebulk.regex('B[RD]-?Mux', 'Blu-?ray-?Mux', value='BluRay')
    rebulk.regex('DVD-?Mux', value='DVD')
    rebulk.regex('WEB-?Mux', 'DL-?WEB-?Mux', 'WEB-?DL-?Mux', 'DL-?Mux', value='WEB-DL')

    # https://github.com/guessit-io/guessit/issues/315
    rebulk.regex('WEB-?DL-?Rip', value='WEBRip')
    rebulk.regex('WEB-?Cap', value='WEBCap')
    rebulk.regex('DSR', 'DS-?Rip', 'SAT-?Rip', 'DTH-?Rip', value='DSRip')
    rebulk.regex('LDTV', value='TV')
    rebulk.regex('DVD\d', value='DVD')

    return rebulk


def screen_size():
    """Screen size property.

    :return:
    :rtype: Rebulk
    """
    # https://github.com/guessit-io/guessit/issues/319
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE)
    rebulk.defaults(name='screen_size', validator=seps_surround)
    rebulk.regex(r'(?:\d{3,}(?:x|\*))?720phd', value='720p')
    rebulk.regex(r'(?:\d{3,}(?:x|\*))?1080phd', value='1080p')

    rebulk.regex('NetflixUHD', value='4k')

    return rebulk


def other():
    """Other property.

    :return:
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name='other', validator=seps_surround)

    # https://github.com/guessit-io/guessit/issues/300
    rebulk.regex(r'Re-?Enc(?:oded)?', value='Re-Encoded')

    rebulk.regex('DIRFIX', value='DirFix')
    rebulk.regex('INTERNAL', value='Internal')
    rebulk.regex(r'(?:HD)?iTunes(?:HD)?', value='iTunes')
    rebulk.regex('HC', value='Hardcoded subtitles')

    rebulk.rules(ValidateHardcodedSubs)

    return rebulk


def size():
    """Size property.

    Remove when https://github.com/guessit-io/guessit/issues/299 is fixed.
    :return:
    :rtype: Rebulk
    """
    def format_size(value):
        return re.sub(r'(?<=\d)[\.](?=[^\d])', '', value.upper())

    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name='size', validator=seps_surround)
    rebulk.regex(r'\d+\.?[mgt]b', r'\d+\.\d+[mgt]b', formatter=format_size, tags=['release-group-prefix'])

    return rebulk


def language():
    """Language property.

    :return:
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash])
    rebulk.defaults(name='language', validator=seps_surround)
    rebulk.regex('SPANISH-?AUDIO', r'(?:Espa[.]ol-)?castellano', value=babelfish.Language('spa'))
    rebulk.regex('german-dubbed', 'dubbed-german', value=babelfish.Language('deu'))
    rebulk.regex('dublado', value='und', formatter=babelfish.Language)

    return rebulk


def subtitle_language():
    """Subtitle language property.

    :return:
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE | re.UNICODE, abbreviations=[alt_dash])
    rebulk.defaults(name='subtitle_language', validator=seps_surround)

    # special handling
    rebulk.regex(r'Legenda(?:s|do)?@PT-?BR', value=babelfish.Language('por', 'BR'))
    rebulk.regex(r'Legenda(?:s|do)?@PT(?!-?BR)', value=babelfish.Language('por'))
    rebulk.regex('Subtitulado@ESP(?:a[nñ]ol)?@Spanish', 'Subtitulado@ESP(?:a[nñ]ol)?', value=babelfish.Language('spa'),
                 conflict_solver=lambda match, other: other if other.name == 'language' else '__default__')

    # undefined language
    rebulk.regex('Subtitles', 'Legenda(?:s|do)', 'Subbed', 'Sub(?:title)?s?@Latino',
                 value='und', formatter=babelfish.Language, tags='subtitle.undefined')

    rebulk.rules(RemoveSubtitleUndefined)

    return rebulk

def audio_channels():
    """Audio channels property.

    :return:
    :rtype: Rebulk
    """
    rebulk = Rebulk().regex_defaults(flags=re.IGNORECASE, abbreviations=[dash]).string_defaults(ignore_case=True)
    rebulk.defaults(name='audio_channels')

    # https://github.com/guessit-io/guessit/issues/328
    rebulk.string('7.1ch', value='7.1')
    rebulk.string('5.1ch', value='5.1')
    rebulk.string('2.0ch', value='2.0')

    return rebulk


class ValidateHardcodedSubs(Rule):
    """Validate HC matches."""

    priority = 32
    consequence = RemoveMatch

    def when(self, matches, context):
        """Remove `other: Hardcoded subtitles` if there's no subtitle_language matches as a neighbour.

        :param matches:
        :type matches: rebulk.match.Matches
        :param context:
        :type context: dict
        :return:
        """
        to_remove = []
        for hc in matches.named('other', predicate=lambda match: match.value == 'Hardcoded subtitles'):
            next_match = matches.next(hc, predicate=lambda match: match.name == 'subtitle_language', index=0)
            if next_match and not matches.holes(hc.end, next_match.start,
                                                predicate=lambda match: match.value.strip(seps)):
                continue

            previous_match = matches.previous(hc, predicate=lambda match: match.name == 'subtitle_language', index=0)
            if previous_match and not matches.holes(previous_match.end, hc.start,
                                                    predicate=lambda match: match.value.strip(seps)):
                continue

            to_remove.append(hc)

        return to_remove


class RemoveSubtitleUndefined(Rule):
    """Remove subtitle undefined when there's an actual subtitle language."""

    priority = POST_PROCESS - 1000
    consequence = RemoveMatch

    def when(self, matches, context):
        """Remove subtitle undefined if there's a subtitle language as a neighbor.

        :param matches:
        :type matches: rebulk.match.Matches
        :param context:
        :type context: dict
        :return:
        """
        to_remove = []
        for und in matches.tagged('subtitle.undefined'):
            next_match = matches.next(und, predicate=lambda match: match.name == 'subtitle_language', index=0)
            if not next_match or matches.holes(und.end, next_match.start,
                                               predicate=lambda match: match.value.strip(seps)):
                previous_match = matches.previous(und,
                                                  predicate=lambda match: match.name == 'subtitle_language', index=0)
                if not previous_match or matches.holes(previous_match.end, und.start,
                                                       predicate=lambda match: match.value.strip(seps)):
                    continue

            to_remove.append(und)

        return to_remove
