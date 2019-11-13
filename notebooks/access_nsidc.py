#----------------------------------------------------------------------
# Functions for customization and access notebook
#
# In Python a module is just a collection of functions in a file with
# a .py extension.
#
# Functions are defined using:
#
# def function_name(argument1, arguments2,... keyword_arg1=some_variable) 
#     '''A docstring explaining what the function does and what
#        arguments it expectes.
#     '''
#     <commands>
#     return some_value  # Not required unless you need to return a value
#
#----------------------------------------------------------------------

def print_cmr_metadata(entry, fields=['dataset_id', 'version_id']):
    '''This is a docstring.

    Prints metadata from query to CMR collections.json

    entry - Metadata entry for a dataset
    fields - list of metdata fields to print
    '''
    print(', '.join([f"{field}: {entry[field]}" for field in fields]))

