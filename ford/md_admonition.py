"""
Admonition Preprocessor
=======================

Markdown preprocessor for dealing with FORD style admonitions. See
:ref:`sec-note-boxes` for details on using these in Ford docs.

A preprocessor, :py:class:`AdmonitionPreprocessor`, converts Ford style
``@note`` into something that the existing `markdown admonition
extension`_ can handle. This is mostly a matter of making sure the
note body is indented correctly. The conversion to HTML is done with a
customised processor, :py:class:`FordAdmonitionProcessor`

.. _markdown admonition extension:
   https://python-markdown.github.io/extensions/admonition/

"""

import re
from dataclasses import dataclass
from typing import ClassVar, List
from textwrap import indent

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.extensions.admonition import AdmonitionProcessor

ADMONITION_TYPE = {
    "note": "info",
    "warning": "warning",
    "todo": "success",
    "bug": "danger",
    "history": "history",
}
"""Mapping of Ford note types to markdown's admonition types"""


class AdmonitionExtension(Extension):
    """Admonition extension for Python-Markdown."""

    def extendMarkdown(self, md):
        """Add Admonition to Markdown instance."""
        md.registerExtension(self)
        md.parser.blockprocessors.deregister("admonition", strict=False)
        md.preprocessors.register(AdmonitionPreprocessor(md), "admonition-pre", 105)
        md.parser.blockprocessors.register(
            FordAdmonitionProcessor(md.parser), "admonition", 105
        )


class FordMarkdownError(RuntimeError):
    """Format an error when processing markdown, giving some context"""

    def __init__(
        self,
        message: str,
        line_number: int,
        lines: List[str],
        start: int,
        end: int,
        context: int = 4,
    ):
        line_start = line_number - context
        line_end = line_number + context
        line_context = lines[line_start:line_end]
        num_len = len(f"{line_end}")
        text_with_line_numbers = [
            f"{line_start + n + 1:{num_len}d}: {line}"
            for n, line in enumerate(line_context)
        ]
        marker = f"{' ' * (num_len + 2 + start)}{'^' * (end - start)}"
        text_with_line_numbers.insert(context + 1, marker)
        text = indent("\n".join(text_with_line_numbers), "    ")
        super().__init__(f"{message}:\n\n{text}")


class FordAdmonitionProcessor(AdmonitionProcessor):
    """Customised version of the `Python markdown`_ extension.

    Uses our CSS class names for each specific note type.

    .. _Python markdown:
       https://python-markdown.github.io/extensions/admonition/
    """

    CLASSNAME = "alert"
    CLASSNAME_TITLE = "alert-title h4"
    RE = re.compile(r"""(?:^|\n)@note ?(?P<klass>[\w\-]+) *(?:\n|$)""")

    def get_class_and_title(self, match):
        """Get the CSS class and title for this admonition

        Title is the note class, while the CSS class is looked up
        in the list of note types (`ADMONITION_TYPE`)

        """
        klass = match["klass"].lower()
        return f"alert-{ADMONITION_TYPE[klass]}", klass.capitalize()


class AdmonitionPreprocessor(Preprocessor):
    """Markdown preprocessor for dealing with FORD style admonitions.

    This preprocessor converts the FORD syntax for admonitions to
    the markdown admonition syntax.

    A FORD admonition starts with ``@<type>``, where ``<type>`` is one of:
    ``note``, ``warning``, ``todo``, ``bug``, or ``history``.
    An admonition ends at (in this order of preference):

    1. ``@end<type>``, where ``<type>`` must match the start marker
    2. an empty line
    3. a new note (``@<type>``)
    4. the end of the documentation lines

    The admonitions are converted to the markdown syntax, i.e. ``@note Note``,
    followed by an indented block. Possible end markers are removed, as well
    as empty lines if they mark the end of an admonition.
    """

    INDENT_SIZE: ClassVar[int] = 4
    INDENT: ClassVar[str] = " " * INDENT_SIZE
    ADMONITION_RE: ClassVar[re.Pattern] = re.compile(
        rf"""(?P<indent>\s*)
        @(?P<type>{"|".join(ADMONITION_TYPE.keys())})
        (?P<posttxt>.*)
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    END_RE: ClassVar[re.Pattern] = re.compile(
        rf"""\s*@end(?P<type>{"|".join(ADMONITION_TYPE.keys())})
        \s*(?P<posttxt>.*)?""",
        re.IGNORECASE | re.VERBOSE,
    )
    admonitions: List["Admonition"] = []

    @dataclass
    class Admonition:
        """A single admonition block in the text."""

        #: Admonition type (note, bug, and so on)
        type: str
        #: Line index of start marker
        start_idx: int
        #: Line index where admonition ends
        end_idx: int = -1

    def run(self, lines: List[str]) -> List[str]:
        admonitions = self._find_admonitions(lines)
        return self._process_admonitions(admonitions, lines)

    def _find_admonitions(self, lines: List[str]) -> List[Admonition]:
        """Scans the lines to search for admonitions."""
        admonitions = []
        current_admonition = None

        for idx, line in enumerate(lines):
            if match := self.ADMONITION_RE.search(line):
                if current_admonition:
                    if current_admonition.end_idx == -1:
                        current_admonition.end_idx = idx
                    admonitions.append(current_admonition)
                current_admonition = self.Admonition(type=match["type"], start_idx=idx)

            if end := self.END_RE.search(line):
                if not current_admonition:
                    raise FordMarkdownError(
                        "Note end marker found without start marker",
                        idx,
                        lines,
                        end.start(),
                        end.end(),
                    )

                if end["type"].lower() != current_admonition.type.lower():
                    raise FordMarkdownError(
                        "Type of start and end marker don't match",
                        idx,
                        lines,
                        end.start(),
                        end.end(),
                    )

                current_admonition.end_idx = idx
                admonitions.append(current_admonition)
                current_admonition = None

            if current_admonition is None:
                continue

            if line == "" and current_admonition.end_idx == -1:
                # empty line encountered while in an admonition. We set end_line but don't
                # move it to the list yet since an end marker (@end...) may follow
                # later.
                current_admonition.end_idx = idx

        if current_admonition:
            # We reached the last line and the last admonition wasn't moved to the list yet.
            if current_admonition.end_idx == -1:
                current_admonition.end_idx = idx
            admonitions.append(current_admonition)

        return admonitions

    def _process_admonitions(
        self, admonitions: List[Admonition], lines: List[str]
    ) -> List[str]:
        """Processes the admonitions to convert the lines to the markdown syntax."""

        # We handle the admonitions in the reverse order since
        # we may be deleting lines.
        for admonition in admonitions[::-1]:
            # last line--deal with possible text before or after end marker
            idx = admonition.end_idx
            if end := self.END_RE.search(lines[idx]):
                # Shove anything after the @end into a new paragraph
                if end["posttxt"]:
                    lines.insert(idx + 1, "")
                    lines.insert(idx + 2, end["posttxt"])

                # Remove the @end and possibly the line too if it ends up blank
                lines[idx] = self.END_RE.sub("", lines[idx])
                if lines[idx].strip() == "":
                    del lines[idx]
                else:
                    # New ending is now next line
                    admonition.end_idx += 1

            # Indent any intermediate lines
            end_line = min(len(lines), admonition.end_idx + 1)
            for idx in range(admonition.start_idx + 1, end_line):
                if lines[idx] != "":
                    lines[idx] = self.INDENT + lines[idx]

            idx = admonition.start_idx
            if (match := self.ADMONITION_RE.search(lines[idx])) is None:
                # Something has gone seriously wrong!
                raise FordMarkdownError("Missing start of @note", idx, lines, 0, -1)

            lines[idx] = f"{match['indent']}@note {admonition.type.capitalize()}"
            if posttxt := match["posttxt"]:
                lines.insert(idx + 1, self.INDENT + match["indent"] + posttxt)

        return lines
