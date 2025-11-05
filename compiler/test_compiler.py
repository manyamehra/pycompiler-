import os
import subprocess
from analyse_semantique import compile_code

def test_case(name,source,expected_output=None):
    #Test a single compilation case
    print(f"\n{'='*50}")
    print(f"test:{name}")
    print(f"{'='*50}")

    output_file=f"test_{name}.s"

    try:
        #Compile
        compile_code(source,output_file=output_file)
        print(f"Compilation succesful")

        #Cleanup
        os.remove(output_file)
    
    except Exception as e:
        print(f"Error: {e}")
        return False
    return True 
