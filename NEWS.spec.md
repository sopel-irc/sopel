Sopel's NEWS file was originally used for plainly communicating the list of
changes in each release to humans. After Sopel 6.6.0, a lot of work went into
improving [the website](https://sopel.chat/), and part of that work involved
using the NEWS file to make HTML changelog pages. Since the file was already
Markdown-like, parsing it with a script became the chosen method.

What follows is a description of the syntax conventions used to keep NEWS
easily consumable by the [website build script][dvs]. It uses the common all-
caps RFC terms "MUST", "SHOULD", etc. according to the usual RFC conventions.
Anything set off by one of these is important to follow as it might affect the
website build script's ability to read this file correctly, or effectively
translate it into HTML pages.

  [dvs]: https://github.com/sopel-irc/sopel.chat/blob/master/document_versions.py

----

The whole file SHOULD be hard-wrapped to 80 columns for ease of reading/updating
in terminal-based editors, but failure to wrap a few lines here and there
shouldn't break anything.

Each section MUST start with a Setext-style top-level heading (underlined using
`=`). There SHOULD always be two blank lines before and one blank line after
this release heading. The text MUST read `Changes between a.b.c and x.y.z` (it
is used to break this single file into one-page-per-version for the website).
Example release section heading, including blank line spacing:

```Markdown


Changes between 1.0.0 and 1.0.1
===============================

```

After that, there MAY be an optional prose section for general notes about the
release, notices about upcoming changes, migration instructions, etc. If
present, this section SHOULD end with a horizontal rule (`----`). Example:

```Markdown
Sopel 1.0.1 is a bugfix release with numerous small changes that add up to a big
improvement in the user experience when combined.

----

```

Each version's section SHOULD be subdivided into "Module changes", "Core
changes", and "API changes"—in that order. The three subsections MUST be marked
"up" (get it? because it's Mark*down*) as Setext-style second-level headings
(underlined using `-`). Each subsection heading SHOULD have one blank line above
and below. Subsections that remain empty after filling in the changes (see
below) SHOULD be omitted from the final release section.

Within the "changes" subsections, the convention is to present relevant line-
items from the release's commit log or list of merged pull requests as a
Markdown bulleted list (items begin with `* `; line continuations are indented
with two spaces to align with the start of that item's text). The subsection
names are mostly self-explanatory. Things that concern end users should go in
"Module" or "Core" changes; things that only affect developers (of modules or of
Sopel itself) should go in "API changes"—which, again, should appear last.

The change lists MAY have nested levels of bullets to convey additional details.
Each level should be indented by two additional spaces.

Command names (both Sopel and shell commands), Python package names, config
setting names, and anything else "code-like" SHOULD be marked up `as such` with
backticks. In most cases this doesn't really matter, but it really does ease
readability of the generated HTML pages. And some things (for example,
sequential hyphens in change entries about CLI options like `--config`) will
come out wrong without the backticks.

Example subsections and placeholder change entries:

```Markdown

Module changes
--------------

* foo module's `.bar` command won't baz any more
* eggs module removed
  * replaced by a new bacon module

Core changes
------------

* IRC `foo` intent handled correctly

API changes
-----------

* `sopel.spam` is now deprecated and will be removed in Sopel 2.0. Use the new
  tools in `sopel.sausage` introduced in 0.9.0 instead.

```

Links MAY be included anywhere it is appropriate, using any Markdown link style.
Implicitly referenced links (like `[link text][]`) are preferred because they
make the text easier to read; however, explicit references (`[link text][id]`)
are OK too if the same link is used in multiple places.

Link reference definitions SHOULD be placed at the end of the subsection where
they are first used, before any following horizontal rule or heading.

Link reference definitions SHOULD be indented with two spaces, EXCEPT directly
after lists:

```Markdown
  [link text]: https://sopel.chat/ "Optional title"
```

After a list, DO NOT indent link references. The last list item will be
incorrectly formatted when the HTML for Sopel's website is rendered.

Link references MUST be defined within each release section, even if you are
reusing a previously defined link, because nothing outside the release section
will be accessible when the file is split into HTML pages for the website.
(N.B.: If this becomes overly tedious, the script could be made smarter; link
references "SHOULD" be indented to help with this in case it needs to happen.)
