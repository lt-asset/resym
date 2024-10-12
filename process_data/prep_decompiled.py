import argparse
import os
from utils import *
from typing import Dict, List
from tqdm import tqdm
import re
from error import ParseError

HEADER = '#include "/home/ReSym/clang-parser/defs.hh"\n'

def process_funname(raw_addr:str) -> str:
    # sub_401220 -> 401220
    if raw_addr == 'main':
        return raw_addr
    match = re.search(r'^sub_([\w\d]+)$', raw_addr)
    if match:
        return match.group(1)
    else:
        return None



        
def hex_to_decimal(hex_str : str) -> int:
    # Check if the input hex string is valid
    if not re.match(r'^-?[0-9a-fA-F]+$', hex_str):
        return None

    # Convert the hex string to decimal
    decimal_num = int(hex_str, 16)
    return decimal_num



def extract_comments(fun_content:List[str]) -> List[Dict]:
    var_decl_pattern = r'^(.+?\s+\**)(\S+);\s+\/\/(.*)$'  # <g1> <g2>; // <g3>
    rbp_offset_pattern = r'\[rbp(-[\d\w]+?)h\]'   # [rbp-<g1>h]
    array_name_pattern = r'^(.*?)\[(\d+)\]$'  # <g1>[<g2>]


    var_decl_info = []
    for line in fun_content:
        match = re.match(var_decl_pattern, line.strip())
        if match:
            var_type = match.group(1).strip()
            var_name = match.group(2).strip()
            comment = match.group(3).strip()

            # parse var_name (handle array)
            array_name_match = re.match(array_name_pattern, var_name)
            if array_name_match:
                var_name = array_name_match.group(1) 
                array_size = int(array_name_match.group(2))  
            else:
                array_size = None

            # parse comment, get rbp offset
            rbp_offset = None
            rbp_offset_match = re.search(rbp_offset_pattern, comment)
            if rbp_offset_match:
                rbp_offset = rbp_offset_match.group(1)
            
            rbp_offset_dec = hex_to_decimal(rbp_offset) if rbp_offset is not None else None

            # handle *
            ptr_level = var_name.count("*")
            var_name = var_name.replace('*', "")

            var_decl_info.append({
                'name': var_name,
                'type': var_type, 
                'comment': comment.strip().replace('"',"`").replace("'", '`'),
                'array_size': array_size,
                'ptr_level': ptr_level,
                'rbp_offset_hex': rbp_offset, 
                'rbp_offset_dec': rbp_offset_dec,
                'original_line': line.strip().replace('"',"`").replace("'", '`')
            })
           

    return var_decl_info

def parse_signature(file_content:List[str], funname:str=None) -> List[Dict]:
    arg_info = []
    if not funname: 
        pattern = r'((sub_[\d\w]+)|main)\((.*?)\)'  # <g1> (<g2>)
    else:
        pattern = r'(({})|main)\((.*?)\)'.format(funname)  # <g1> (<g2>)

    if isinstance(file_content, str):
        file_content = file_content.split('\n')
    found = False
    for l_index in range(3):
        line = file_content[l_index]
        match = re.search(pattern, line)
        if match:
            funname, arglist = match.group(1), match.group(3)
            found = True
            break
    if not found:
        raise ParseError('Fail to parse the signature.')
    
    if not arglist:
        return arg_info
    
    arg_pattern = r'^(.*?)(a\d+)$'    # xxxx a1: <g1><g2>
    arg_pattern2 = r'^((struct\s|const\s)?\w+?\s+\*?)(\w+)$'  # (struct/const )?xxx *?<g3>
    for arg in arglist.split(','):
        if arg.strip() == '...':
            arg_info.append({
                'name': arg.strip(),
                'original_line': arg.strip()
            })
            continue

        if arg.strip() == 'void':
            continue

        arg_match = re.match(arg_pattern, arg.strip())
        if arg_match:
            
            argtype, argname = arg_match.group(1).strip(), arg_match.group(2)
            
        else:
            arg_match = re.match(arg_pattern2, arg.strip())
            if arg_match:
                argtype, argname = arg_match.group(1).strip(), arg_match.group(3)
            else:
                raise ParseError(f'Cannot find the declaration of argument {arg.strip()}.')


        if argname in arg_info:
            raise ParseError(f'{argname} duplicate')
        
        
        arg_info.append({
            'name': argname,
            'type': argtype, 
            'original_line': arg.strip()
        })
            
    return arg_info



def prep_decompiled(src_dir_or_file, file_save_dir, parsed_save_dir):
    if os.path.isdir(src_dir_or_file):
        files = [os.path.join(src_dir_or_file, f) for f in get_file_list(src_dir_or_file)]
    else:
        files = [src_dir_or_file]



    for f in tqdm(files, disable=len(files)==1):
        if not f.endswith(".decompiled"):
            continue
        fname = os.path.basename(f)

        decompiled = read_json(f)

        for fun in decompiled:
            dex_addr, funname, code = fun['addr'], fun['funname'], fun['code']
            if funname.startswith('sub_'):
                addr = process_funname(funname).upper()
            else:
                addr = str(hex(dex_addr))[2:].upper()
                

            code_with_header = HEADER + code

            new_fname = fname.replace('.decompiled', '-' + str(addr))+'.c'
            write_file(os.path.join(file_save_dir,new_fname), code_with_header)

            # parse decompiled
            code_lines = code.split('\n')
            try:
                if funname.startswith('sub_'):
                    arg_info: List[Dict] = parse_signature(code_lines)
                else:
                    if funname.startswith('.'):
                        funname = funname[1:]

                    arg_info: List[Dict] = parse_signature(code_lines, funname=funname)
                var_info: List[Dict] = extract_comments(code_lines)
            except ParseError as e:
                print(f'{fname} - {funname}: {e.msg}')
                continue
            except Exception as e:
                print(f'[ERROR] (parse_decomplied) Other error {fname} - {funname}: {e}')
                continue
            save_data = {'argument': arg_info, 'variable': var_info}

            var_fname = fname.replace('.decompiled', '-' + str(addr) + '_var.json')
            dump_json(os.path.join(parsed_save_dir, var_fname), save_data)




if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src_dir_or_file')
    parser.add_argument('file_save_dir')
    parser.add_argument('parsed_save_dir')
    args = parser.parse_args()
    prep_decompiled(args.src_dir_or_file, args.file_save_dir, args.parsed_save_dir)

    