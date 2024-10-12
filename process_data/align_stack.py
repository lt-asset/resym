import argparse
import os
from utils import *
from tqdm import tqdm
from error import FileAlignException, VarAlignException
from typing import List, Dict
import re

def get_decompiled_code(code_dir, binname, hex_addr) -> str:

    fpath = os.path.join(code_dir, f"{binname}-{hex_addr.upper()}.c")
    if not os.path.exists(fpath):
        raise FileAlignException(f'File {fpath} not found.')
    file_content = read_file(fpath, readlines=True)
    return ''.join(file_content[1:]).strip()

def array_element_cnt (array_dims: List[int]) -> int:
    cnt = 1
    for dim in array_dims:
        cnt *= dim

    return cnt

def struct_field_info(type_attr) -> (int, List[str], List[int]):
    assert type_attr['is_struct']
    cnt = len(type_attr['struct_fields'])
    sizes = []
    names = []
    
    for field in type_attr['struct_fields']:
        sizes.append(field['field_attr']['total_size'])
        names.append(field['field_name'])

    return cnt,names,sizes


def get_group_sizes (head_varname: str, var_data) -> List[int]:
    # get the sizes of the head and (consecutive) children (except the last one) based on the locations

    group_indices : List[int] = []
    for i, var in enumerate(var_data):
        if var['name'] == head_varname:
            group_indices.append(i)  # head

        if 'aligned_head' in var and var['aligned_head'] == head_varname:
            group_indices.append(i)  # child
    
    locs = []
    for i in group_indices:
        loc = var_data[i]['rbp_offset_dec']
        locs.append(loc)
    locs = sorted(locs)

    sizes = []
    for i in range(len(locs) -1):
        sizes.append(locs[i+1] - locs[i])

    assert len(sizes) + 1 == len(locs)
   
    return sizes


def type_available(var_attr):
    # unavailable resason: union or od.c `u`
    if var_attr['DW_AT_type'] == '<unknown>' or var_attr['type_attr']['type_name'] is None:
        return False

    return True

def process_pointer(type_attr):
    assert type_attr['is_pointer'] 
    type_name = type_attr['type_name']  # has "*"
    pts_level = max(1, type_name.count("*"))  # at least one

    if type_name.count("*") == 0:
        type_name += '*'
    return type_name
    
    base_type = type_attr['base_type_name']
    point_to_type_name = type_attr['point_type_name']
    pointee_base_type = base_type if base_type is not None else point_to_type_name

    pointee_pts_level = pointee_base_type.count("*")

    if pointee_pts_level >= pts_level:
        raise VarAlignException(f'pointee_pts_level >= pts_level (type: {type_name}, pointee: {pointee_base_type})')

    # remove * in pointee_base_type
    pointee_base_type = pointee_base_type.replace("*", "").strip()

    pointee_base_type = pointee_base_type
    
    return pointee_base_type  + '*'*pts_level
    

def process_array(type_attr) -> str:
    
    element_type = type_attr['type_name']
    array_type_str = element_type
    for dim in type_attr['array_dims']:
        array_type_str += f"[{dim}]"
    return array_type_str


def align_single_helper(type_attr, varname):
    base_type_name = type_attr['base_type_name']
    type_name = type_attr['type_name']


    if type_attr['type_name'] is None and  type_attr['base_type_name'] is None:
        raise VarAlignException(f'{varname} - both type and base_type are None')


    label_size = type_attr['total_size']
    # determine label_type
    if type_attr['is_pointer']:
        label_type = process_pointer(type_attr)
    elif type_attr['is_array']:
        label_type = process_array(type_attr)
    elif type_attr['is_struct']:
        label_type = 'struct ' + type_name
    else:
        label_type = type_attr['total_size']

    if label_type is None:
        raise VarAlignException(f'{varname} label_type somehow is None??? (type: {type_name}, basetype: {base_type_name}, type_attr: {type_attr})')

    return label_type, label_size


def align_single_var(arg_data):
    # used for arg and single var
    type_attr = arg_data['aligned']['Attr']['type_attr']
    label_name = arg_data['aligned']['Attr']['DW_AT_name']
    label_tag = 'B'   # for argument, always B
    
    

    label_type, label_size = align_single_helper(type_attr, label_name)

    return label_name, label_type, label_size, label_tag


def get_child (head_varname:str, var_data: List[Dict])-> List[int]:
    children = []
    for i, var in enumerate(var_data):
        if 'aligned_head' in var and var['aligned_head'] == head_varname:
            children.append(i)
    return children

def get_head_idx (var_data: List[Dict],  arg_idx) -> int:
    # determine head
    if var_data[arg_idx]['aligned_tag'] == 'B':
        assert var_data[arg_idx]['head']
        head_idx = arg_idx
    elif var_data[arg_idx]['aligned_tag'] == 'I':
        # not likely go into this branch
        assert var_data[arg_idx]['aligned_head']
        head_name = var_data[arg_idx]['aligned_head']
        for i, var in enumerate(var_data):
            if var['name'] == head_name:
                head_idx = i
                break
    else:
        assert False

    return head_idx


def align_group(var_data: List[Dict], head_idx:int, children_indices: List[int]) -> Dict[int, Dict]:
    head_attr = var_data[head_idx]['aligned']['Attr']['type_attr']
    head_name = var_data[head_idx]['name']
    ret_label = {}  
    complex_var = {'array':[], 'struct': []}
    if head_attr['is_pointer'] + head_attr['is_array'] + head_attr['is_struct'] == 0:
        raise VarAlignException(f'{head_name} - head of single var')
    
    if head_attr['is_pointer'] + head_attr['is_array'] + head_attr['is_struct'] != 1:
        raise VarAlignException(f'{head_name} - head has multiple properties')

    if head_attr['is_pointer']:
        raise VarAlignException(f'{head_name} - head that is a pointer')

    elif head_attr['is_array']:
        element_cnt = array_element_cnt(head_attr['array_dims'])
        
        if 'base_type_name' not in head_attr or 'base_size' not in head_attr:
            raise VarAlignException(f'{head_name} - array (group) no base type found.')

        label_name = var_data[head_idx]['aligned']['Attr']['DW_AT_name']
        label_type = head_attr['type_name']

    
        ret_label[head_idx] = {'name': label_name, 'type': label_type}
        for varidx in children_indices:
            ret_label[varidx] = {
                'name': '-',
                'type': '-',
            }
        complex_var['array'].append([var_data[i]['name'] for i in [head_idx] + children_indices])
    
        
    elif head_attr['is_struct']:
    
        struct_varname = var_data[head_idx]['aligned']['Attr']['DW_AT_name']
        struct_name = head_attr['type_name']

        

        for varidx in [head_idx] + children_indices:
            label_name = struct_varname 
            label_type = f'struct {struct_name}'
            ret_label[varidx] = {
                'name': label_name if varidx==head_idx else '-',
                'type': label_type if varidx==head_idx else '-',
            }
        complex_var['struct'].append([var_data[i]['name'] for i in [head_idx] + children_indices])

    return ret_label, complex_var


def process_args(arg_data: List[Dict], fname:str) -> List[Dict]:
    # fname for debug purpose only
    # return modified arg_data
    for i, arg in enumerate(arg_data):
        try:
            label = {}
            argname = arg['name']
            if "aligned" not in arg:
                continue
       
            if not type_available(arg['aligned']['Attr']):
                raise VarAlignException(f'Type of {argname} is not available.')
            label_name, label_type, label_size, label_tag = align_single_var(arg)
            label = {
                'name': label_name,
                'type': label_type,

            }

            arg_data[i]['label'] = label   # update arg_data

        except VarAlignException as e:
            print(f'Warning: {fname} - {argname}: {e.msg}')
            continue
    return arg_data


def process_vars(var_data: List[Dict], fname:str) -> List[Dict]:
    def _update_complex_var(old_complex_var, new_complex_var):
        for arr_l in new_complex_var['array']:
            if 'array' not in old_complex_var:
                old_complex_var['array'] = []
            old_complex_var['array'].append(arr_l)
        for struct_l in new_complex_var['struct']:
            if 'struct' not in old_complex_var:
                old_complex_var['struct'] = []
            old_complex_var['struct'].append(struct_l)
        return old_complex_var


    visited = set()  # set of indices
    complex_var = {}
    for i, var in enumerate(var_data):
        try:
            label = {}
            varname = var['name']
            if i in visited:
                continue
            
            if "aligned" not in var:
                continue
            
            if not type_available(var['aligned']['Attr']):
                raise VarAlignException(f'Type of {varname} is not available.')

            if ('head' in var and var['head']) or var['aligned_tag'] == "I":
                # align group
                head_idx = get_head_idx(var_data, i)
                children_indices = get_child(var_data[head_idx]['name'], var_data)
                for j in [head_idx] + children_indices:
                    visited.add(j)

                group_labels, tmp_complex_var = align_group(var_data, head_idx, children_indices)
                complex_var = _update_complex_var(complex_var, tmp_complex_var)
                for varidx, label in group_labels.items():
                    var_data[varidx]['label'] = label
            else:
                # individual variable
                visited.add(i)
                label_name, label_type, label_size, label_tag = align_single_var(var)


                var_data[i]['label'] = {
                    'name': label_name,
                    'type': label_type,
                }


        except VarAlignException as e:
            print(f'Warning: {fname} - {varname}: {e.msg}')
            continue
    return var_data, complex_var





def align_stack(align_data:Dict, binname, hex_addr, code_dir, save_dir):

    fname = f"{binname}-{hex_addr}"
    code:str = get_decompiled_code(code_dir, binname, hex_addr)
    args: List[Dict] = process_args(align_data['argument'], fname)  
    vars, complex_var = process_vars(align_data['variable'], fname)

    align_data['argument'] = args
    align_data['code'] = code
    align_data['variable'] = vars
    align_data['complex_var'] = complex_var

    dump_json(os.path.join(save_dir, fname + '.json'), align_data)
    return align_data
   


def gen_vardecoder_data(fname, align_stack_data, save_dir, ignore_complex=False) -> bool:
    # fname: <binname>-<addr>

    def _process_label(fname, align_data)->(int, Dict):
        label_cnt = 0
        label = {}
        all_compelx_vars = []
        for _, var_groups in align_data['complex_var'].items():
            for var_group in var_groups:
                all_compelx_vars += var_group

        for var in align_data['argument'] + align_data['variable']:
            if 'label' in var:
                if 'type' not in var:
                    print(f"Cannot process variable {var['name']} from {fname}")
                    continue
                var_ida_type = var['type']
                varname = var['name']
                if ignore_complex and varname in all_compelx_vars:
                    continue
                label[var['name']] = list(var['label'].values())
                label_cnt += 1


        if label_cnt == 0:
            return label_cnt, None

        code = align_data['code']
        funname = align_data['funname']
        complex_var = align_data['complex_var']
        save_data = {
            'label': label,
            'code': code,
            'funname': funname,
            'complex_var' : complex_var
        }

        return label_cnt, save_data


    def _gen_prompt(label_data: Dict)-> (str, str):
        vars = list(label_data['label'].keys())
        code = label_data['code']
        
        code = code.strip()
        prompt = 'In the following decompiled C program, what are the original name, data type, data size and tag of variables ' 
        prompt += ', '.join([f'`{v}`' for v in vars]) + '?\n'
        prompt += f'```\n{code.strip()}\n```'
        oracle = ''
        for var in vars:
            name, ty = label_data['label'][var]
            oracle += f'{var}: {name}, {ty}\n'
        oracle = oracle.strip()
        

        return prompt, code,  oracle


    success = False

    label_cnt, label_data = _process_label(fname, align_stack_data)
    if label_cnt == 0:
        return success
    
    success = True
    prompt, code, oracle = _gen_prompt(label_data)
    

    save_data = {
        'code': code, 
        'prompt': prompt,
        'output': oracle, 
        'funname': label_data['funname'], 
        'label': label_data['label']
        }
    if label_data['complex_var']:
        save_data['complex_var'] = label_data['complex_var']
    dump_json(os.path.join(save_dir, fname+'.json'), save_data)
    
    return success


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src_dir')
    parser.add_argument('code_dir', help='the folder (.../decompiled) of the decompiled code')
    parser.add_argument('save_dir')
    parser.add_argument('--bin', required=False, default=None)
    args = parser.parse_args()
    
    main(args.src_dir, args.code_dir, args.save_dir, target_bin = args.bin)

