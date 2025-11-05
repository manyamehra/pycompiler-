import sys
import argparse
from analyse_semantique import compile_code

def main():
    parser=argparse.ArgumentParser(description='Compiler for subset of C')
    parser.add_argument('input',help='Input source file')
    parser.add_argument('-o','--output',help='Output assembly file', default='output.s')
    parser.add_argument('--ast', action='store_true', help='Show AST')
    parser.add_argument('--run', action='store_true', help='Run with MSM after compilation')

    args=parser.parse_args()

    #Read input file
    try:
        with open(args.input,'r') as f:
            source_code=f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.input} not found")
        sys.exit(1)
    
    #Compile
    try:
        compile_code(source_code, output_file=args.output, show_ast=args.ast)
        print(f"Compilation succesful: {args.output}")
    except Exception as e:
        print(f"Compilation error: {e}")
        sys.exit(1)
    
if __name__=="__main__":
    main()