#!/usr/bin/env python2.7
import os
from textwrap import dedent as trim
import imp

def main():
    filenames = []
    this_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(this_dir, 'source', 'modules.rst')
    root_dir = os.path.dirname(this_dir)
    os.sys.path.insert(0,root_dir)
    modules_dir = os.path.join(root_dir, 'modules')
    for fn in os.listdir(modules_dir):
        if fn.endswith('.py') and not fn.startswith('_'):
            filenames.append(os.path.join(modules_dir, fn))

    filenames.append(os.path.join(root_dir, 'coretasks.py'))
    
    with open(output_file, 'w') as f:
        f.write(trim("""\
        Module Documentation
        ====================
        
        This page contains documentation for all modules within Willie's main
        modules directory. If you have added modules without rebuilding the
        documentation, or are using a secondary modules directory, those modules
        will not be shown here.
        
        Modules
        =======
        """))
        for filename in filenames:
            document_module(filename, f)

def document_module(module_file, f):
    try: module = imp.load_source(os.path.basename(module_file)[:-3], module_file)
    except Exception, e:
        print ("Error loading %s: %s\nThis module will not be documented."
               % (module_file, e))
    else:
            #try:
            f.write('\n%s\n%s\n'%(module.__name__, '-'*len(module.__name__)))
            f.write(module.__doc__ or '')
            if hasattr(module, 'configure'):
                process_configure(f, module)
            for obj in dir(module):
                if (hasattr(getattr(module, obj), 'commands')
                        or hasattr(getattr(module, obj), 'rule')):
                    process_command(f, getattr(module, obj))
            
            #except Exception, e:
            #print ("Error while documenting %s: %s\nThis module will not be documented" % (module_file, e))

def process_configure(f, module):
    if not module.configure.__doc__: return
    
    f.write('\n.. py:attribute:: Configuration Variables\n')
    

def process_command(f, func):
    #Handle customized function name
    if not hasattr(func, 'name'):
        name = func.__name__
    else:
        name = func.name
    
    #Handle docstring and example
    doc = '\n'+(func.__doc__ or '*No documentation found.*')
    if hasattr(func, 'example'):
        example = func.example
        example = example.replace('$nickname', 'Willie')
        doc = doc + '\n\n*Example:* %s' % example

    f.write('\n.. py:attribute:: %s\n' % name)
    f.write(tabulate(doc)+'\n')

def tabulate(string, indent_by=1):
    return string.replace('\n', '\n'+('\t'*indent_by))

if __name__ == '__main__':
    main()
