#!/usr/bin/env python2.7
"""
Willie module documentation utility
This script creates (either Markdown or reST) files, documenting the commands
and module configuration options in a Willie instance.

Copyright 2012 Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
import os
from textwrap import dedent as trim
import imp

def main():
    filenames = []
    this_dir = os.path.dirname(os.path.abspath(__file__))
    config_vals_file = os.path.join(this_dir, 'source', 'modules.md')
    commands_file = os.path.join(this_dir, 'source', 'commands.md')
    root_dir = os.path.dirname(this_dir)
    os.sys.path.insert(0,root_dir)
    modules_dir = os.path.join(root_dir, 'modules')
    for fn in os.listdir(modules_dir):
        if fn.endswith('.py') and not fn.startswith('_'):
            filenames.append(os.path.join(modules_dir, fn))

    filenames.append(os.path.join(root_dir, 'coretasks.py'))
    
    commands = []
    
    with open(config_vals_file, 'w') as f:
        f.write(trim("""\
        This page contains documentation for all modules within Willie's main
        modules directory. If you have added modules without rebuilding the
        documentation, or are using a secondary modules directory, those modules
        will not be shown here.
        
        Modules
        =======
        """))
        for filename in filenames:
            c = document_module(filename, f)
            if c:
                commands.extend(c)
    
    commands.sort()
    
    with open(commands_file, 'w') as f:
        f.write("| Commands | Purpose | Example | Module |\n")
        f.write("| -------- | ------- | ------- | ------ |\n")
        for c in commands:
            process_command(f, c)

def document_module(module_file, f):
    try: module = imp.load_source(os.path.basename(module_file)[:-3], module_file)
    except Exception, e:
        print ("Error loading %s: %s\nThis module will not be documented."
               % (module_file, e))
    else:
            #try:
            commands = []
            if hasattr(module, 'configure'):
                f.write('\n%s\n%s\n'%(module.__name__, '-'*len(module.__name__)))
                process_configure(f, module)
            
            for obj in dir(module):
                func = getattr(module, obj)
                if (hasattr(func, 'commands')):
                    if not hasattr(func, 'name'):
                        name = func.__name__
                    else:
                        name = func.name
                    setattr(func, 'module_name', module.__name__)
                    commands.append((name, func))
            
            #except Exception, e:
            #print ("Error while documenting %s: %s\nThis module will not be documented" % (module_file, e))
            
            return commands

def process_configure(f, module):
    if not module.configure.__doc__: return
    
    f.write('\n.. py:attribute:: Configuration Variables\n')
    

def process_command(f, func):
    name = func[0]
    func = func[1]
    
    purpose = (func.__doc__ or '*No documentation found.*').replace('\n', '<br>')
    if hasattr(func, 'example'):
        example = func.example.replace('$nickname', 'Willie')
    else:
        example = ''

    commands = '.'+'<br>.'.join(func.commands) #TODO rules
    module = func.module_name
    line = "| %s | %s | %s | %s |\n" % (commands, purpose, example, module)
    f.write(line)

def tabulate(string, indent_by=1):
    return string.replace('\n', '\n'+('\t'*indent_by))

if __name__ == '__main__':
    main()
