import argparse
import os
from utils import *
from tqdm import tqdm
from error import FileAlignException, VarAlignException
from typing import List, Dict
from gen_train_field import gen_fielddecoder_data

def search_by_name(align_data, varname):
    for arg_data in align_data['argument']:
        if arg_data['name'] == varname:
            return arg_data
    for var_data in align_data['variable']:
        if var_data['name'] == varname:
            return var_data
    return None


def align_offset(var_data_type_attr, offset) -> Dict:
    if not var_data_type_attr['point_to_struct_fileds']:
        raise VarAlignException("Error: not point_to_struct_fileds data available")
    curr_size = 0
    for field in var_data_type_attr['point_to_struct_fileds']:
        if field['field_attr']['total_size'] is None:
            raise VarAlignException(f"VarAlignError: total_size of field {field['field_name']} is None")
        if curr_size == offset:
            return field
        if curr_size > offset: 
            raise VarAlignException(f"VarAlignError: Corresponding field (offset {offset}) not found. (point to mid)")

        curr_size += int(field['field_attr']['total_size'])

    if curr_size > offset:
        raise VarAlignException(f"VarAlignError: Corresponding field (offset {offset}) not found. (point to mid)")
    if curr_size <= offset:
        raise VarAlignException(f"VarAlignError: Corresponding field (offset {offset}) not found. (offset larger than struct size)")


def select_zero_offset(field_access_data) -> List[str]:
    available_vars = set()  # variables that has real beyond access  (offset > 0) 
    for access in field_access_data:
        if int(access['offset']) > 0:
            available_vars.add(access['varName'])

    selected_vars = set()
    selected_expr = set()
    for access in field_access_data:
        if int(access['offset']) == 0 and access['varName'] in available_vars and access['varName'] not in selected_vars:
            if '[0]' in access['expr']:
                selected_expr.add(access['expr'])
                selected_vars.add(access['varName'])
    

    for access in field_access_data:
        if int(access['offset']) == 0 and access['varName'] in available_vars and access['varName'] not in selected_vars:
            selected_expr.add(access['expr'])
            selected_vars.add(access['varName'])

    return selected_expr
    
def align_heap_access(fname, align_data, field_access_data) -> List[Dict]:
    def _align_heap_access_helper(access):
        it_save_data = access
        varname = access['varName']
        var_data = search_by_name(align_data, varname)
        if var_data is None:
            raise VarAlignException("VarAlignError: no var data in the align file.") 
        if 'aligned' not in var_data:
            raise VarAlignException("Warning: no variable is aligned") 
        
        

        align_varname = var_data['aligned']['Attr']['DW_AT_name']
        align_var_data_type_attr = var_data['aligned']['Attr']['type_attr']
        align_type = var_data['aligned']['Attr']['DW_AT_type']

        if not align_type:
            raise VarAlignException("No field type found.") 
        
        if 'lhsPointeeSize' not in access:
            raise VarAlignException("lhsPointeeSize not accessible") 
        offset = max(1, int(access['lhsPointeeSize'])) * int(access['offset']) 


        it_save_data['aligned'] = {
            'varName': align_varname,
            'real_type': var_data['aligned']['Attr']['DW_AT_type'],
            'type': align_type,
            'totalSize': align_var_data_type_attr['point_to_size'],
        }


        if align_var_data_type_attr['is_pointer'] and align_var_data_type_attr['point_to_struct']:
            aligned_field = align_offset(align_var_data_type_attr, offset)

            it_save_data['aligned']['fieldName'] = aligned_field['field_name']
            field_type = aligned_field['field_attr']['type_name']
            if not field_type:
                raise VarAlignException("No field type found. (struct)") 
            if aligned_field['field_attr']['array_dims']:
                # when field is an array
                it_save_data['aligned']['field_array_dims'] = aligned_field['field_attr']['array_dims']

                field_type += f"[-]"  # leave the size of the array empty, fill in during aggregation
                
            it_save_data['aligned']['real_fieldType'] = aligned_field['field_attr']['type_name']
            it_save_data['aligned']['fieldType'] = field_type
            it_save_data['aligned']['fieldSize'] = aligned_field['field_attr']['total_size']
        else:
            # consider it as a array    
            it_save_data['aligned']['fieldName'] = "-"
            field_type = align_var_data_type_attr['point_type_name']
            if not field_type:
                raise VarAlignException("No field type found. (array)") 
            it_save_data['aligned']['fieldType'] = field_type
            it_save_data['aligned']['real_fieldType'] = align_var_data_type_attr['point_type_name']
            it_save_data['aligned']['fieldSize'] = align_var_data_type_attr['point_to_size']

        return it_save_data


    save_data = []
    seen = set()

    
    # first iter, skip all zero-offset cases
    for access in field_access_data:
        if int(access['offset']) == 0:
            continue
        key = (access['varName'], access['offset'])
        if key in seen:
            continue
        try:
            it_save_data = _align_heap_access_helper(access)
            save_data.append(it_save_data)
            seen.add(key)
        except VarAlignException as e:
            print(f"{fname} - {access['varName']} - {e.msg}")
            continue

    if not save_data:
        return save_data

    # second iter, only handle zero-offset cases
    expr_selected_zero_offset = select_zero_offset(field_access_data)

    for access in field_access_data:
        if int(access['offset']) == 0 and access['expr'] not in expr_selected_zero_offset:
            continue 
        try:
            it_save_data = _align_heap_access_helper(access)
            save_data.append(it_save_data)

        except VarAlignException as e:
            print(f"{fname} - {access['varName']} - {e.msg}")
            continue

    return save_data


def main(align_folder, filed_access_folder, save_dir, target_bin):
    success_cnt = 0
    fail_cnt = 0
    unavailable = 0
   

    for f in tqdm(get_file_list(align_folder), disable=target_bin):
        if not f.endswith('.json'):
            continue

        if target_bin and not f.startswith(target_bin):
            continue

        fname = f.replace('.json', '')
        try:
            align_data = read_json(os.path.join(align_folder, f))
            save_data = {
                'funname': align_data['funname'],
                'code': align_data['code']
            }
            if not os.path.exists(os.path.join(filed_access_folder, f)):
                unavailable += 1
                print(f"Cannot find the beyond access info file in {os.path.join(filed_access_folder, f)}")
                continue
            field_access_data = read_json(os.path.join(filed_access_folder, f))

            aligned_data = align_heap_access(f, align_data, field_access_data)
            if aligned_data: 
                save_data['aligned'] = aligned_data

                success_cnt += 1 
            else:
                unavailable += 1
                continue
        except FileAlignException as e:
            print(f'Error: {os.path.join(align_folder, f)} - {e.msg}')
            fail_cnt += 1
            continue
        except Exception as e:
            print(f'[ERROR] (align heap) Other error {os.path.join(align_folder, f)} - {e}')
            fail_cnt += 1
            continue

        gen_fielddecoder_data(fname, save_data, save_dir)
    print(f'Success: {success_cnt}, Fail: {fail_cnt}, Unavailable: {unavailable}')


    
if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('align_dir')
    parser.add_argument('filed_access_folder')
    parser.add_argument('save_dir')
    parser.add_argument('--bin', required=False, default=None)
    args = parser.parse_args()
    
    main(args.align_dir, args.filed_access_folder, args.save_dir, target_bin = args.bin)
