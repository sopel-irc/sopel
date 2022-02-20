================
Do it with style
================

.. Custom role definitions to apply custom style to inline text

.. role:: red
    :class: red

.. role:: boldred
    :class: bold red

.. role:: underline
    :class: underline

.. role:: strike
    :class: strike

.. role:: bolditalic
    :class: bold italic

.. role:: spoiler
    :class: spoiler


When the bot talks, replies, or acts, it can do so with style: colors,
**bold**, *italic*, :underline:`underline`, :strike:`strikethrough`, or
``monospace``. IRC formatting works with control codes, bytes you can use to
tell IRC clients how to display some part of the text.

.. seealso::

    If you want to know more about IRC formatting in general and some of its
    limitations, `the modern IRC documentation`__ may be of interest to you.

    .. __: https://modern.ircdocs.horse/formatting.html

However, dealing with control codes yourself is not the most dev-friendly
approach, hence the :mod:`sopel.formatting` module. It contains various
functions to help you create styled text.

Text styles
===========

Let's dive into examples, starting with :func:`~sopel.formatting.bold` text::

    from sopel import formatting

    bot.say(formatting.bold('This is some bold text!'))

This will output a line like this:

    <Sopel> **This is some bold text!**

You can use them with Python string formatting::

    emphasis = formatting.bold('important')
    bot.say('And here is the %s part.' % emphasis)

To get that kind of output:

    <Sopel> And here is the **important** part.

And you can use multiple style functions together, for example with the
:func:`~sopel.formatting.italic` function::

    word = formatting.italic('very')
    emphasis = formatting.bold('%s important' % word)
    bot.say('And here is the %s part.' % emphasis)

To get a result that looks like this:

    <Sopel> And here is the :bolditalic:`very` **important** part.

Colored styles
==============

Colorized text is a bit more complicated, and Sopel tries to provide helpful
functions and constants for that: the :func:`~sopel.formatting.color` function
and the :class:`~sopel.formatting.colors` class.

The ``color`` function takes a line of text and a foreground color. It also
accepts an optional background color that uses the same color codes. The color
codes are listed by the ``colors`` class, and can be used like this::

    bot.say(formatting.color('Red text.', formatting.colors.RED))

The above example should produce this output:

    <Sopel> :red:`Red text.`

You can combine colors and styles, like this::

    big = formatting.color(
        formatting.bold('WARNING'), formatting.colors.RED)
    small = formatting.italic('warning')
    bot.say('[%s] This is a %s.' % (big, small))

So you get a similar result as:

    <Sopel> [:boldred:`WARNING`] This is a *warning*.

If you want to prevent spoilers, you could be tempted to take advantage of
the background color::

    spoiler = formatting.color(
        'He was the killer.',
        formatting.colors.BLACK,
        formatting.colors.BLACK,
    )
    bot.say(spoiler)

And expect this (you need to select the text to read it):

    <Sopel> :spoiler:`He was the killer.`

Note that not all combinations of foreground and background colors are happy
ones, and you should be mindful of using too many unnecessary colors.
