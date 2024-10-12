#!/bin/bash

# Ensure at least one argument is provided (the required parameter)
if [ -z "$1" ]; then
    echo "Error: Missing required parameter."
    echo "Usage: $0 <required_param> [--field]"
    exit 1
fi
source_dir=$1    
field_flag=""
clean_flag=""

# Check if the optional "field" parameter is provided
if [[ "$2" == "--field" || "$3" == "--field" ]]; then
    echo "Extracting both stack variables and field access information."
    field_flag="--field"
else
    echo "Extracting stack variables only."
fi


# Check if the optional "clean" parameter is provided
if [[ "$2" == "--clean" || "$3" == "--clean" ]]; then
    echo "Clean flag is set. Will clean intermediate results after processing."
    clean_flag="--clean"
fi


MAX_PROC=20
check_interval=1

check_dir_exist() {
    target_dir=$1
    # Check if the source directory exists
    if [ ! -d "$target_dir" ]; then
        echo "Directory '$target_dir' does not exist."
        exit 1
    fi
}

create_dir() {
    target_dir=$1

    # Check if the destination directory exists, create it if necessary
    if [ ! -d "$target_dir" ]; then
        mkdir -vp "$target_dir"
        if [ $? -ne 0 ]; then
            echo "Failed to create destination directory '$target_dir'."
            exit 1
        fi
    fi
}


create_and_clean_dir() {
    target_dir=$1
    create_dir $target_dir
    # Check if the directory contains any files before trying to remove them
    if [ "$(ls -A "$target_dir")" ]; then
        rm "$target_dir"/*
        if [ $? -ne 0 ]; then
            echo "Warning: Could not remove some files in '$target_dir'."
        fi
    # else
    #     echo "The directory '$target_dir' is empty."
    fi
}


bin_dir="$source_dir/bin"
decompiled_dir="$source_dir/decompiled"
check_dir_exist $bin_dir
check_dir_exist $decompiled_dir

decompiled_files_dir="$source_dir/decompiled_files/"
decompiled_vars_dir="$source_dir/decompiled_vars"
debuginfo_subprograms_dir="$source_dir/debuginfo_subprograms"
align_var="$source_dir/align"
train_var="$source_dir/train_var"
logs_dir="$source_dir/logs"

create_and_clean_dir $decompiled_files_dir
create_and_clean_dir $decompiled_vars_dir
create_and_clean_dir $debuginfo_subprograms_dir
create_and_clean_dir $align_var
create_and_clean_dir $train_var
create_and_clean_dir $logs_dir

if [ -n "$field_flag" ]; then
    commands_dir="$source_dir/commands"
    field_access_dir="$source_dir/field_access/"
    train_field="$source_dir/train_field"
    create_and_clean_dir $commands_dir
    create_and_clean_dir $field_access_dir
    create_and_clean_dir $train_field
fi


process_file() {
    local FILE=$1

    binname=$(basename "$FILE")
    
    # Check if the corresponding decompiled file exists, if not, skip processing
    if [ ! -f "$decompiled_dir/$binname.decompiled" ]; then
        return
    fi

    python prep_decompiled.py "$decompiled_dir/$binname.decompiled" $decompiled_files_dir $decompiled_vars_dir >> "$logs_dir/parse_decompiled_errors"

    python parse_dwarf.py $bin_dir"/$binname" --save_dir=$debuginfo_subprograms_dir


    if [ -n "$field_flag" ]; then
        python init_align.py $decompiled_vars_dir $debuginfo_subprograms_dir $decompiled_files_dir $align_var $train_var --bin $binname >> "$source_dir/logs/align_errors"


        echo "#!/bin/bash" > "$commands_dir/$binname"_command.sh
        python gen_command.py $decompiled_files_dir "$source_dir" --bin $binname >> "$commands_dir/$binname"_command.sh
        bash "$commands_dir/$binname"_command.sh >> "$logs_dir/clang_errors" 2>&1

        python align_field.py $align_var $field_access_dir $train_field --bin $binname >> $logs_dir/align_field_errors
    else
        python init_align.py $decompiled_vars_dir $debuginfo_subprograms_dir $decompiled_files_dir $align_var $train_var --bin $binname --ignore_complex >> "$source_dir/logs/align_errors"
    fi

    echo "$binname" >> "$donefiles"
}


# Create an array of all files in the bin directory
files=($bin_dir/*)
jobs_cntr=0
jobs_to_run_num=${#files[@]}
donefiles=$source_dir"completed_files"
rm -f $donefiles
touch $donefiles

# Main processing loop with multithreading logic
while ((jobs_cntr < jobs_to_run_num)); do
    # Get the current number of running jobs
    cur_jobs_num=$(wc -l < <(jobs -r))

    # Get the current file to process
    current_file="${files[jobs_cntr]}"

    # Check if the file has already been processed
    if ! grep -q -F "$current_file" "$donefiles"; then
        if ((cur_jobs_num < MAX_PROC)); then
            echo "=== Progress: $jobs_cntr/$jobs_to_run_num ==="
            process_file "$current_file" &
            ((jobs_cntr++))
        else
            sleep "$check_interval"
        fi
    else
        # File already processed, so just increase the counter
        ((jobs_cntr++))
    fi
done

# Wait for all background jobs to complete
wait



if [ -n "$clean_flag" ]; then
    echo "Cleaning intermediate results."
    rm -r $decompiled_files_dir
    rm -r $decompiled_vars_dir
    rm -r $debuginfo_subprograms_dir
    rm -r $align_var
    rm -r $logs_dir
    rm $donefiles
    if [ -n "$field_flag" ]; then
        rm -r $field_access_dir
        rm -r $commands_dir
    fi
fi



if [ -n "$field_flag" ]; then
    echo "Data processing finished. The results can be found in $train_var and $train_field."
else
    echo "Data processing finished. The results can be found in $train_var"
fi
