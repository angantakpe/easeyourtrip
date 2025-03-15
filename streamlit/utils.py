import json
import sys
from typing import Any

def die(data: Any, exit_program: bool = False):
    """
    Debug utility function to print data and optionally exit the program.
    
    Args:
        data: The data to print (can be any type)
        exit_program: Whether to exit the program after printing (default: False)
    """
    print("\n===== DEBUG OUTPUT =====")
    if isinstance(data, (dict, list)):
        try:
            print(json.dumps(data, indent=2, default=str))
        except:
            print(data)
    else:
        print(data)
    print("========================\n")
    
    if exit_program:
        sys.exit(1)