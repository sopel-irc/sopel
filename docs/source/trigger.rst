Triggers
========

A :class:`~.trigger.Trigger` is the main type of user input plugins will see.

Sopel uses :class:`~.trigger.PreTrigger`\s internally while processing
incoming IRC messages. Plugin authors can reasonably expect that their code
will never receive one. They are documented here for completeness, and for the
aid of Sopel's core development.

.. autoclass:: sopel.trigger.Trigger
    :members:

.. autoclass:: sopel.trigger.PreTrigger
    :members:
