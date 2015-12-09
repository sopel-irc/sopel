Submitting Issues
-----------------

When submitting issues to our
[issue tracker](https://github.com/sopel-irc/sopel/issues), it's important
that you do the following:

1. Describe your issue clearly and concisely.
2. Give Sopel the .version command, and include the output in your issue.
3. Note the OS you're running Sopel on, and how you installed Sopel (via your
package manager, pip, setup.py install, or running straight from source)
4. Include relevant output from the log files in ~/.sopel/logs.

Committing Code
---------------
We prefer code to be submitted through GitHub pull requests. We do require that
code submitted to the project be licensed under the Eiffel Forum License v2,
the text of which was distributed with the source code.

In order to make it easier for us to review and merge your code, it's important
to write good commits, and good commit messages. Below are some things you
should do when you want to submit code. These aren't hard and fast rules; we
may still consider code that doesn't meet all of them. But doing the stuff
below will make our lives easier, and by extension make us more likely to
include your changes.

* Commits should focus on one thing at a time. Do include whatever you need to
  make your change work, but avoid putting unrelated changes in the same commit.
  Preferably, one change in functionality should be in exactly one commit.
* pep8ify your code before you commit. We don't worry about line length much
  (though it's good if you do keep lines short), but you should try to follow
  the rest of the rules.
* Test your code before you commit. We don't have a formal testing plan in
  place, but you should make sure your code works as promised before you commit.
* Make your commit messages clear and explicative. Our convention is to place
  the name of the thing you're changing in [brackets] at the beginning of the
  message: the module name for modules, [docs] for documentation files,
  [coretasks] for coretasks.py, [db] for the database feature, and so on.
* Python files should always have `#coding: utf8` as the first line (or the
  second, if the first is `#!/usr/bin/env python`), and
  `from __future__ import unicode_literals` as the first line after the module
  docstring.

Issue Tags
----------
If you're looking to hack on some code, you should consider fixing one of the
issues that has been reported to the GitHub issue tracker. Here's a quick guide
to the tags we use:

* Easyfix           - A great place for a new developer to start off, Easyfix
                      issues are ones which we think will be simple and quick
                      to address.
* Patches Welcome   - Things we don't plan on doing, but which we might be
                      interested to see someone else submit code for
* Bug               - An error or incorrect behavior
* Feature           - A new thing the bot should be able to do
* Tweak             - A minor change to something the bot already does, like
                      making something's output prettier, improving the
                      documentation on something, or addressing technical debt
* Tracking          - An ongoing process that involves lots of changes in lots
                      of places. Often also a Tweak.
* Low Priority      - Things we'll get around to doing eventually
* Medium Priority   - Things that need to be done soon
* High Priority     - Things that should've been done yesterday
* Tests             - Issues regarding the testing unit in tests/
* Windows           - Windows-specific bugs are labelled as such
