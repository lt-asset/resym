from elftools.elf.elffile import ELFFile
import argparse
import io
from elftools.dwarf.locationlists import (
    LocationEntry, LocationExpr, LocationParser)
from elftools.dwarf.descriptions import (
    describe_DWARF_expr, set_global_machine_arch)
from pathlib import Path
from typing import Dict, List
from utils import *
from tqdm import tqdm
import re


POINTER_SIZE = 8
PRINT_TREE = False   # for debugging purpose
DEBUG = False   # for debugging purpose

def show_loclist(loclist, dwarfinfo, indent, cu_offset):
    """ Display a location list nicely, decoding the DWARF expressions
        contained within.
    """
    d = []
    for loc_entity in loclist:
        if isinstance(loc_entity, LocationEntry):
            d.append('%s <<%s>>' % (
                loc_entity,
                describe_DWARF_expr(loc_entity.loc_expr, dwarfinfo.structs, cu_offset)))
        else:
            d.append(str(loc_entity))
    return '\n'.join(indent + s for s in d)



def read_elf(fpath):
    # Read the ELF file data into memory
    with open(fpath, 'rb') as f:
        elfdata = f.read()

    # Create a file-like object from the byte data
    elffile = ELFFile(io.BytesIO(elfdata))
    return elffile





def print_tree(s):
    if PRINT_TREE:
        print(s)

def debug_print(s):
    if DEBUG:
        print(s)
# global dict, from offset to its DieDecription
STRUCT_DICT = {}


class DieDecription():
    def __init__(self, istype:bool=False, type_name:str=None, base_type_name:str=None, base_size:int=None, total_size:int=None, is_array:bool=False, is_struct:bool=False, is_pointer:bool=False, point_type_name:str=None, point_to_struct:bool=False, point_to_size:int=None, point_to_struct_fileds:List[Dict]=[], array_dims:List[int]=None, struct_fields:List[Dict]=[]):
        self.istype = istype
        self.type_name = type_name
        self.base_type_name = base_type_name
        self.base_size = base_size
        self.total_size = total_size 
        self.is_array = is_array
        self.is_struct = is_struct
        self.is_pointer = is_pointer
        self.point_type_name = point_type_name
        self.point_to_struct = point_to_struct
        self.point_to_struct_fileds:List[Dict] = point_to_struct_fileds
        self.point_to_size = point_to_size  # the size of the object it points to
        self.array_dims = array_dims
        self.struct_fields:List[Dict] = struct_fields


    def attr_dict(self, skip_recursive=False) -> Dict:
        attr_dict = self.__dict__.copy()  # copy the dict so we don't change the original
        if skip_recursive:
            attr_dict['struct_fields'] = []
            attr_dict['point_to_struct_fileds'] = []
        else:
            if self.struct_fields:
                # Convert the struct fields into their string representation
                attr_dict['struct_fields'] = [ {k: v.attr_dict() if isinstance(v, DieDecription) else v for k, v in d.items()} for d in self.struct_fields]

            if self.point_to_struct_fileds:
                attr_dict['point_to_struct_fileds'] = [ {k: v.attr_dict(skip_recursive=True) if isinstance(v, DieDecription) else v for k, v in d.items()} for d in self.point_to_struct_fileds]
        return attr_dict

    def __str__(self) -> str:
        return f"DieDescription({self.attr_dict()})"





def process_addr(raw_addr:str) -> str:
    # 0x501992 -> 501992
    match = re.search(r'^0x([\w\d]+)$', raw_addr)
    if match:
        return match.group(1)
    else:
        assert False


def main(fpath, save_dir = None):

    def describe_die(die, die_dict) -> DieDecription:   
        def _get_type(tmp_die) -> DieDecription:
            if 'DW_AT_type' in tmp_die.attributes:
                target_type_die = die_dict.get(CU.cu_offset + tmp_die.attributes['DW_AT_type'].value)
                if target_type_die is not None:
                    return describe_die(target_type_die, die_dict)
            return DieDecription()


        # Check STRUCT_DICT first
        if die.offset in STRUCT_DICT:
            return STRUCT_DICT[die.offset]



        die_description = DieDecription()

        # Handle the size calculation
        byte_size = die.attributes.get('DW_AT_byte_size')
        if byte_size is not None:
            byte_size = byte_size.value
            die_description.total_size = byte_size


        if die.tag == 'DW_TAG_array_type':
            die_description.is_array = True
            element_d = _get_type(die)

            array_dims = []
            array_dim_unknown = False
            for child_die in die.iter_children():
                if child_die.tag == "DW_TAG_subrange_type":
                    upper_bound_attr = child_die.attributes.get('DW_AT_upper_bound')
                    if upper_bound_attr is not None:
                        if isinstance(upper_bound_attr.value, int):
                            array_dims.append(upper_bound_attr.value + 1)
                        else:
                            array_dim_unknown = True
                            break

            if element_d.base_size:
                die_description.base_size = element_d.base_size
                if array_dim_unknown:
                    die_description.total_size = None
                else:
                    die_description.total_size = element_d.base_size
                    for array_dim in array_dims:
                        die_description.total_size *= array_dim

            
            die_description.type_name = element_d.type_name
            die_description.base_type_name = element_d.base_type_name
            if not array_dim_unknown:
                die_description.array_dims = array_dims
           

        elif die.tag == 'DW_TAG_structure_type':
            die_description.is_struct = True
            
            if 'DW_AT_name' in die.attributes:
                die_description.type_name = die.attributes['DW_AT_name'].value.decode()

            STRUCT_DICT[die.offset] = die_description


            die_description.struct_fields = []
            for child_die in die.iter_children():
                if child_die.tag == 'DW_TAG_member':
                    member_name = child_die.attributes.get('DW_AT_name').value.decode() if 'DW_AT_name' in child_die.attributes else "<unknown>"  #TODO: should be fresh name
                    member_d = _get_type(child_die)
                    die_description.struct_fields.append({'field_name': member_name, 'field_attr': member_d})
            STRUCT_DICT[die.offset] = die_description


        elif die.tag == 'DW_TAG_base_type':
            if 'DW_AT_name' in die.attributes:
                die_description.base_type_name = die.attributes['DW_AT_name'].value.decode()
                die_description.type_name = die_description.base_type_name
                die_description.base_size = byte_size
        elif die.tag == 'DW_TAG_restrict_type':
            # ignore
            tmp_d = _get_type(die)
            die_description = tmp_d
                
        else:
            tmp_d = _get_type(die)
            die_description.base_type_name = tmp_d.base_type_name
            die_description.type_name = tmp_d.type_name
            die_description.base_size = tmp_d.base_size
            die_description.total_size = byte_size or tmp_d.total_size

            

            if die.tag == 'DW_TAG_pointer_type':
                die_description.is_pointer = True
                type_name = tmp_d.type_name if tmp_d.type_name else "void"
                die_description.point_type_name = type_name
                die_description.point_to_size = tmp_d.total_size
                die_description.type_name = f'{type_name}*'
                die_description.total_size = byte_size or POINTER_SIZE
                if tmp_d.is_struct:
                    die_description.point_to_struct = True
                    die_description.point_to_struct_fileds = tmp_d.struct_fields

            else:
                die_description = tmp_d


                if die.tag == 'DW_TAG_const_type':
                    type_name = tmp_d.type_name if tmp_d.type_name else "void"
                    if 'const' not in type_name:
                        die_description.type_name = f'const {type_name}'
                    else:
                        die_description.type_name = f'{type_name}'
                        

                if 'DW_AT_name' in die.attributes:
                    die_description.type_name = die.attributes['DW_AT_name'].value.decode()

            

        debug_print(die.tag)
        debug_print(die_description)
        return die_description
     
    def die_info_rec(die, indent_level='    ') -> Dict:
        """ A recursive function for showing information about a DIE and its
            children.
        """
        print_tree(indent_level + 'DIE tag=%s' % die.tag)
        curr_tag_info = {'Tag': die.tag, 'Attr': {}, 'child': []}


        if die.tag == 'DW_TAG_subprogram':
            if 'DW_AT_name' not in die.attributes:
                curr_tag_info['funname'] = '<unknown>'
            else:
                funname = die.attributes['DW_AT_name'].value.decode()
                if funname.startswith('single_binary_main_'):
                    funname = 'main'
                curr_tag_info['funname'] = funname
            if 'DW_AT_low_pc' not in die.attributes:
                curr_tag_info['fun_start_addr'] = '<unknown>'
            else:
                func_addr = die.attributes['DW_AT_low_pc'].value
                curr_tag_info['fun_start_addr'] = hex(func_addr)
        
        
        child_indent = indent_level + '  '
        for attr in die.attributes.items():
            attr_name, attr_value = attr
            assert attr_name not in curr_tag_info['Attr']
            description = print_attr_val(attr_name, attr_value)
            if description is None:
                continue
            curr_tag_info['Attr'][attr_name] = description.type_name if description.type_name is not None else '<unknown>'
            print_tree(child_indent + '|_' + '%s=%s' % (attr_name, curr_tag_info['Attr'][attr_name]))
            if description.istype:
                curr_tag_info['Attr']['type_attr'] = description.attr_dict()
              

        for child in die.iter_children():
            curr_tag_info['child'].append(die_info_rec(child, child_indent))


        return curr_tag_info

    def print_attr_val(attr_name, attr_value) -> DieDecription:
        ret_d = DieDecription()
        if attr_name == 'DW_AT_decl_file':
            line_program = dwarfinfo.line_program_for_CU(CU)
            file_name = line_program['file_entry'][attr_value.value - 1].name
            ret_d.type_name = file_name.decode()
            return ret_d

        elif attr_name == 'DW_AT_type' and 'ref' in attr_value.form:
           
            type_die = global_die_dict.get(CU.cu_offset + attr_value.value )
            if type_die is not None:
                type_description = describe_die(type_die, global_die_dict)
                ret_d = type_description
                ret_d.istype = True
                return ret_d
            else:
                ret_d.istype = True
                return ret_d

        elif loc_parser.attribute_has_location(attr_value, CU['version']):
            loc = loc_parser.parse_from_attribute(attr_value, CU['version'])
            # We either get a list (in case the attribute is a
            # reference to the .debug_loc section) or a LocationExpr
            # object (in case the attribute itself contains location
            # information).
            if isinstance(loc, LocationExpr):
                loc_val = describe_DWARF_expr(loc.loc_expr, dwarfinfo.structs, CU.cu_offset)
            elif isinstance(loc, list): 
                # do not handle this case
                return None
            ret_d.type_name = loc_val
            return ret_d
        else:
            if isinstance(attr_value.value, bytes):
                ret_d.type_name = attr_value.value.decode()
             
            else:
                ret_d.type_name = attr_value.value
            return ret_d



    def _find_subprogram(json_block, binname):
        if json_block['Tag'] == 'DW_TAG_subprogram' and 'funname' in json_block and 'fun_start_addr' in json_block:
            if json_block['funname'] != "<unknown>" and json_block['fun_start_addr'] != "<unknown>":
                # functions strcat/strcpy have addr as unknown
                curr_addr = process_addr(json_block['fun_start_addr'])
                unique_addr = binname + '-' + curr_addr.upper()
                if unique_addr not in visited_addr:
                    visited_addr.add(unique_addr)   
                dump_json(os.path.join(save_dir, unique_addr +'.json'), json_block)
        for child in json_block['child']:
            _find_subprogram(child, binname)




    file_list = []
    if os.path.isdir(fpath):
        file_list = [os.path.join(fpath, f) for f in get_file_list(fpath)]
    else:
        file_list = [fpath]

    
    for f in tqdm(file_list, disable = len(file_list)==1):
        STRUCT_DICT = {} # init struct_dict
        debug_info ={}

        elffile = read_elf(f)
        if not elffile.has_dwarf_info():
            print('file has no DWARF info')
            return
        # get_dwarf_info returns a DWARFInfo context object, which is the
        # starting point for all DWARF-based processing in pyelftools.
        dwarfinfo = elffile.get_dwarf_info()
        
        # The location lists are extracted by DWARFInfo from the .debug_loc
        # section, and returned here as a LocationLists object.
        location_lists = dwarfinfo.location_lists()
        # print(location_lists)  # None

        # This is required for the descriptions module to correctly decode
        # register names contained in DWARF expressions.
        set_global_machine_arch(elffile.get_machine_arch())

        # Create a LocationParser object that parses the DIE attributes and
        # creates objects representing the actual location information.
        loc_parser = LocationParser(location_lists)


        global_die_dict = {} 
        for CU in dwarfinfo.iter_CUs():
            for die in CU.iter_DIEs():
                global_die_dict[die.offset] = die

        # Traverse every DIE (Debugging Information Entry) in the .debug_info section
        for CU in tqdm(dwarfinfo.iter_CUs(), disable = len(file_list)==1):
            top_DIE = CU.get_top_DIE()
            curr_file_path = Path(top_DIE.get_full_path()).as_posix()

            debug_print(CU.cu_offset)         

            debug_info[curr_file_path] = die_info_rec(top_DIE)
           

            binname = os.path.basename(f)
            visited_addr = set()
            for cu in debug_info:
                _find_subprogram(debug_info[cu], binname)

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fpath')
    parser.add_argument('--save_dir', default=None, help='Optional save directory')
    args = parser.parse_args()

    main(args.fpath, args.save_dir if args.save_dir is not None else None)

    

