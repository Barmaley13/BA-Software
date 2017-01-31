#!/usr/bin/python
"""
Script that starts the gate.
For more detailed information refer to documentation under ~/gate_data/docs
"""

### INCLUDES ###
from gate.common import OPTIONS_PARSER


### MAIN ###
if __name__ == '__main__':
    # Get system options from options parser
    (system_options, args) = OPTIONS_PARSER.parse_args()

    from gate.main import main

    # Run gate
    main(system_options)
