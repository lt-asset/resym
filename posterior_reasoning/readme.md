# Posterior Reasoning Results

This folder contains the final results after applying posterior reasoning, used to reproduce the results in **Table 5** of our paper.


## Contents

- **`results.json`**: A JSON file containing the posterior reasoning results.
- **`eval.py`**: A script to evaluate and display the results from `results.json`.


## Instructions for Evaluation

To evaluate the results and reproduce the findings presented in Table 5 of the paper:

```bash
python eval.py results.json
```



## `results.json` Structure

The `results.json` file contains a dictionary where each key-value pair represents the evaluation of a particular variable in a binary. Here's the structure of an example entry:

```json
"mwarning**KadNode**2e8d7c4309cfa01389d7ccb4986397b29bf23e508049cabee256ea6ff17590b0**sub_413229**v2": {
    "pred": {
        "type": "man_viewer_info_list*",
        "offsets": {
            "0": {
                "size": 8,
                "name": "next",
                "type": "man_viewer_info_list*"
            },
            "8": {
                "size": 8,
                "name": "info",
                "type": "char*"
            }
        }
    },
    "gt": {
        "type": "peer*",
        "offsets": {
            "0": {
                "size": 8,
                "name": "next",
                "type": "peer*"
            },
            "8": {
                "size": 8,
                "name": "addr_str",
                "type": "char*"
            }
        }
    }
}
```

### Key Structure

Each key in the JSON file is formatted using the `**` separator and has the following components: author name, project name, binary name, function name, and variable name.


### Value Structure

Each value contains two main components:
- **`pred`** (predicted layout): The predicted layout of the variable after applying posterior reasoning. It includes:
  - **type**: The predicted type of the variable (i.e., struct type).
  - **offsets**: A dictionary where each key represents an offset, and the value contains:
    - **size**: The predicted size of the field.
    - **name**: The predicted name of the field.
    - **type**: The predicted type of the field.
    
- **`gt`** (ground truth layout): The ground truth layout of the variable, structured similarly to `pred`.
