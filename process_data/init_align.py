from utils import *
import argparse
from tqdm import tqdm
import os
from typing import List, Dict
import re
from error import FileAlignException, VarAlignException
from align_stack import align_stack, gen_vardecoder_data

OFFSET = 16   
DEBUG = False


def debug_print(s):
    if DEBUG:
        print(s)


def decrement_hex(hex_str: str) -> str:
    # Convert the hexadecimal string to an integer
    num = int(hex_str, 16)
    
    # Decrement the integer by 1
    num -= 1
    
    # Convert the integer back to a hexadecimal string
    # [2:] is used to remove the '0x' prefix
    hex_str = hex(num)[2:]
    
    return hex_str





def extract_var_from_subprog (subprog_file: Dict) -> List:
    # get all vars from subprogram file (json) as a List
    all_vars = []
    def _helper(sf: Dict) -> List:
        for child in sf['child']:
            if child['Tag'] == 'DW_TAG_formal_parameter' or child['Tag'] == 'DW_TAG_variable':
                all_vars.append({'Tag': child['Tag'], 'Attr': child['Attr']}) # removing child
            if child['child']:
                _helper(child)

    _helper(subprog_file)
    return all_vars


def parse_loc(dw_at_location: str) -> int:
    loc_pattern = r'^\(DW_OP_fbreg:\s+(-?\d+)\)$'  # (DW_OP_fbreg: <g1>)
    match = re.search(loc_pattern, dw_at_location)
    if not match:
        return None
    else:
        return int(match.group(1))


def get_varmap_subprog (subprog_var_list : List, fname: str):
    # extract a mapping from address to var info 
    
    arglist = []  # [arginfo]
    argmap = {}
    varmap = {}  # addr -> varinfo

    for var in subprog_var_list:
        
        try:
            varname = None
            if 'DW_AT_name' not in  var['Attr'] or var['Attr']['DW_AT_name'] is None or var['Attr']['DW_AT_name'] == '<unknown>':
                raise VarAlignException(f"Name not found")
                # due to inline definitions (DW_TAG_inlined_subroutine)
            
            varname = var['Attr']['DW_AT_name']
            
            if 'DW_AT_location' not in var['Attr']:   # error
                raise VarAlignException(f"No location information")

            loc = parse_loc(var['Attr']['DW_AT_location'])
            if loc is None: # error
                raise VarAlignException(f"Cannot parse location: {var['Attr']['DW_AT_location']}")   # e.g., some var/sizes determined by dynamical values (e.g., scanf)
                # usually caused by static/global/dynamically determined vars

            if var['Tag'] == 'DW_TAG_formal_parameter':
                if loc + OFFSET in argmap:# error
                    raise FileAlignException(f'Entry {loc + OFFSET} already exist in argmap')
                arglist.append(var)
                argmap[loc + OFFSET] = var
            else:   # DW_TAG_variable
                if loc + OFFSET in varmap:# error
                    raise FileAlignException(f'Entry {loc + OFFSET} already exist in varmap')
                
            varmap[loc + OFFSET] = var
        except VarAlignException as e:
            print(f"Warning: {fname} - {varname}:  {e.msg}, Skip.")
            continue
    return arglist, argmap, varmap
        
def get_varmap_decompiled (decompiled_var_info: Dict):
    arglist = []  
    varmap = {}   # addr -> varinfo
    for var in decompiled_var_info['variable']:
        if 'rbp_offset_dec' in var and var['rbp_offset_dec'] is not None:
            varmap [var['rbp_offset_dec']] = var

    arglist = decompiled_var_info['argument']
    return arglist, varmap

def align_args (subprog_arglist:List, decompiled_arglist: List, is_main:bool) -> List:
    # modify decompiled_arglist in place
    if len(subprog_arglist) != len(decompiled_arglist):
        if is_main and len(decompiled_arglist)==3 and (len(subprog_arglist)==2 or len(subprog_arglist)==0):  
            # only ignore the alignment error when it is a main function and there are three arguments
            pass
        else:
            raise VarAlignException("Argument counts don't match. Skip all arguments")

    assert len(decompiled_arglist) >= len(subprog_arglist), f'ismain: {is_main}, {len(decompiled_arglist)} <= {len(subprog_arglist)}'
    for i in range(len(subprog_arglist)):
        decompiled_arglist[i]['aligned'] = subprog_arglist[i]

    return decompiled_arglist

def align_params(subprog_varmap : Dict, subprog_argmap: Dict, decompiled_varmap: Dict, decompiled_varlist: List, fname: str)-> Dict:
    # both subprog_varmap and decompiled_varmap are from addr to varinfo
    # modify decompiled_varlist in place
    def _find_head(var_loc):
        debug_print('varloc: '+ str(var_loc))
        sorted_addr = sorted(list(subprog_varmap.keys()))
        for i, loc in enumerate(sorted_addr):
            if loc < var_loc and  loc in decompiled_varmap:
                varsize = subprog_varmap[loc]['Attr']['type_attr']['total_size']
                if varsize is not None and loc + varsize > var_loc:
                    return loc
        
        raise VarAlignException(f"Fail to find the head for variable {var['name']}")

    for addr, var in decompiled_varmap.items():
        if addr in subprog_varmap:
            decompiled_varmap[addr]['aligned_tag'] = "B"
            decompiled_varmap[addr]['aligned'] = subprog_varmap[addr]
        elif addr in subprog_argmap:
            decompiled_varmap[addr]['aligned_tag'] = "B"
            decompiled_varmap[addr]['aligned'] = subprog_argmap[addr]
        else:
            try: 
                debug_print(f"{fname} - {var['name']}")
                head_addr = _find_head(addr)
                decompiled_varmap[addr]['aligned_tag'] = "I"
                decompiled_varmap[addr]['aligned_head'] = decompiled_varmap[head_addr]['name']
                decompiled_varmap[head_addr]['head'] = True
            except VarAlignException:
                print(f"Warning: {fname} - {var['name']}'s head not found. Skip")

    # update decompiled_varlist
    name2idx = {}   # decompiled var name  -> idx in `decompiled_varlist`
    for i, var in enumerate(decompiled_varlist):
        name2idx[var['name']] = i
    for addr, var in decompiled_varmap.items():
        idx = name2idx[var['name']]
        decompiled_varlist[idx] = var
    return decompiled_varlist

def align(var_file, subprogram_file, fname, is_main: bool):
    # fname for debug purpose only

    # get arg and var info from subprogs (debug info)
    subprog_vars = extract_var_from_subprog(subprogram_file)
    subprog_arglist, subprog_argmap, subprog_varmap = get_varmap_subprog(subprog_vars, fname)
    # get arg and var info from decompiled code
    decompiled_arglist, decompiled_varmap = get_varmap_decompiled(var_file)


    # align argument
    try:
        debug_print(fname)
        aligned_args: List = align_args(subprog_arglist, decompiled_arglist, is_main)
    except VarAlignException as e:
        aligned_args = decompiled_arglist
        print(f"Warning: {fname} - {e.msg}")

    # align params
    aligned_vars: List = align_params(subprog_varmap, subprog_argmap, decompiled_varmap, var_file['variable'], fname)

    return {'argument': aligned_args, 'variable': aligned_vars, 'funname': subprogram_file['funname'], 'fun_start_addr': subprogram_file['fun_start_addr']} 

def main(var_dir, subprogram_dir, code_dir, align_save_dir, stack_data_save_dir, target_bin, ignore_complex):


    var_files = get_file_list(var_dir)
    error_cnt = 0
    success_cnt = 0
    train_data_cnt = 0
    is_main = False 
    for f in tqdm(get_file_list(subprogram_dir), disable=(target_bin)):
        if not f.endswith('.json'):
            continue

        if target_bin and not f.startswith(target_bin):
            continue

        fname = f.replace('.json', '')
        proj_name, fun_addr = fname.split('-')
        var_fname = proj_name + '-' + fun_addr.upper()  + '_var.json'

        try:

            if var_fname not in var_files:
                raise FileAlignException(f'Cannot find file {var_fname}. Skip')
                continue
            

            var_file = read_json(os.path.join(var_dir, var_fname))
            subprogram_file = read_json(os.path.join(subprogram_dir, f))
            align_data = align(var_file, subprogram_file, f, is_main = is_main)

        except FileAlignException as e:
            print(f'Error: {var_fname} - {e.msg}')
            error_cnt += 1
            continue
        except Exception as e:
            print(f'[ERROR] (init_align) Other error {os.path.join(var_dir, var_fname)} - {e}')
            error_cnt += 1
            continue

        try:
            align_data = align_stack(align_data, proj_name, fun_addr.upper(), code_dir, align_save_dir)
        except FileAlignException as e:
            print(f'Error: {var_fname} - {e.msg}')
            error_cnt += 1
            continue
        except Exception as e:
            error_cnt += 1
            print(f'[ERROR] (align) Other error {var_fname} - {e}')
            continue

        # generate training data
        train_data_generated = gen_vardecoder_data(fname, align_data, stack_data_save_dir, ignore_complex=ignore_complex)
        train_data_cnt += 1

        success_cnt += 1

    print(f'Success: {success_cnt}, Training data generated: {train_data_cnt}, Fail: {error_cnt}')
        
def _test():
    assert parse_loc("(DW_OP_fbreg: -88)") == -88
    assert parse_loc("(DW_OP_fbreg: -112)") == -112
    assert parse_loc("(DW_OP_fbreg: -88); something else") is None

if __name__=='__main__':
    # _test()
    parser = argparse.ArgumentParser()
    parser.add_argument('var_dir', help = 'the folder (.../decompiled_vars) of parsed vars from decompiled code')
    parser.add_argument('subprogram_dir', help = 'the folder (.../debuginfo_subprograms)of the subprograms extracted from dwarf (debug info)')
    parser.add_argument('code_dir')
    parser.add_argument('align_save_dir')
    parser.add_argument('stack_data_save_dir')
    
    parser.add_argument('--bin', required=False, default=None)
    parser.add_argument('--ignore_complex', required=False, default=False, action='store_true', help="ignore variable clusters. Skip the head as well.")
    args = parser.parse_args()

    main(args.var_dir, args.subprogram_dir, args.code_dir, args.align_save_dir, args.stack_data_save_dir, args.bin, args.ignore_complex)

