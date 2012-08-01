"""
this will be the new config file. 
Im leaving the old one as config.old.py for reference
It will work identically to the old one, but hopefully rewriting the code
will allow us to add the features we need, remove the ones we dont
and understand the code better.
The config will be used for initialization variables and things that changes to
shouldnt get carried over from instance to instance
The settings database will be for things that changes to should get carried over
from instance to instance
this is really just a placeholder until we get actual code in here.
"""

class Conig(object):
    def __init__()
        """ makes the Config object with a few default values """
        
        ## nickname for the bot
        self.nickname = Willie
        
        ## server info
        self.server = "irc.example.com"
        self.port = 6667
        self.channels = ["#main"]
        
    ## nifty little helpful wrappers
    def set_attr(self, attr, value): if (value): setattr(self, attr, value)
    def has_attr(self, attr): hasattr(self, attr)
    
    def interactive_add(self, attr, prompt, default=None):
        """
        Ask user in terminal for the value to assign to 'attr'. 
        If 'default' is passed it will be shown in the prompt. assuming 'attr'
        isn't already defined, because then the current value is used instead.
        """
        if self.has_attr(attr):
            default = getattr(self, attr)
        self.set_attr(attr, raw_input(prompt+' [%s]: ' % default) or default)
    
    def add_list(self, attr, message, prompt):
        """
        Ask user in terminal for a list to assign to 'attr'. If 'attr' is 
        already defined, show the user the current values and ask if the user 
        would like to keep them. Regardless, additional values can be entered. 
        """
        print message
        lst = []
        if self.has_attr(attr) and getattr(self, attr):
            m = "You currently have "
            for c in getattr(self, attr): m = m + c + ', '
            if self.option(m[:-2]+'. Would you like to keep them', True):
                lst = getattr(self, attr)
        mem = raw_input(prompt)
        while mem:
            lst.append(mem)
            mem = raw_input(prompt)
        self.set_attr(attr, lst)
            


