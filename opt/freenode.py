#!/usr/bin/env python
"""
freenode.py - Freenode Specific Stuff
Copyright 2008, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

def replaced(phenny, input): 
   command = input.group(1)
   responses = {
      'cp': '.cp has been replaced by .u', 
      'pc': '.pc has been replaced by .u', 
      'unicode': '.unicode has been replaced by .u', 
      'compare': '.compare has been replaced by .gcs (googlecounts)', 
      'map': 'the .map command has been removed; ask sbp for details', 
      'acronym': 'the .acronym command has been removed; ask sbp for details', 
      # 'img': 'the .img command has been removed; ask sbp for details', 
      'v': '.v has been replaced by .val', 
      'validate': '.validate has been replaced by .validate', 
      # 'rates': "moon wanter. moOOoon wanter!", 
      'web': 'the .web command has been removed; ask sbp for details', 
      'origin': ".origin hasn't been ported to my new codebase yet"
      # 'gs': 'sorry, .gs no longer works'
   }
   try: response = responses[command]
   except KeyError: return
   else: phenny.reply(response)
replaced.commands = [
   'cp', 'pc', 'unicode', 'compare', 'map', 'acronym', 
   'v', 'validate', 'thesaurus', 'web', 'mangle', 'origin', 
   'swhack'
]
replaced.priority = 'low'

if __name__ == '__main__': 
   print __doc__.strip()
