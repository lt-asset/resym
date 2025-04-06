# ReSym Artifact

This repository provides artifacts for the paper [**"ReSym: Harnessing LLMs to Recover Variable and Data Structure Symbols from Stripped Binaries"**](https://www.cs.purdue.edu/homes/lintan/publications/resym-ccs24.pdf) (CCS 2024).

🏆 **ACM SIGSAC Distinguished Paper Award Winner**


**Note**: We are actively maintaining/updating our artifacts. Please make sure you are using the latest version.

## Provided Data and Resources

- **Data preparation script**: Located in the `process_data` folder. It generates training data with ground truth symbol information. The script is push-button, and usage instructions are provided in the folder.
- **Binary files and decompiled code**: Available on [Zenodo](https://zenodo.org/records/13923982) (`ReSym_rawdata`). This includes raw binary files and corresponding decompiled code we used in this project:
     - `bin/`: Contains raw **non-stripped binary files** with debugging information.
     - `decompiled/`: Decompiled code from **fully stripped** binaries.
     - `metadata.json`: Metadata for the binaries, including project information.
     - **Note**: You can generate annotations using the provided scripts in this repository.
- **Training/inference scripts**: Found in the `training_src` folder for VarDecoder and FieldDecoder models.
- **Training, testing, and prediction data**: Available on [Zenodo](https://zenodo.org/records/13923982) (`ReSym_data`). This includes: training data, testing data, and prediction results for FieldDecoder and VarDecoder. 
- **Model checkpoints**: Fine-tuned VarDecoder and FieldDecoder model checkpoints are available on [Zenodo](https://zenodo.org/records/13923982).
- **Final results**: Posterior reasoning results for recovering user-defined data structures in folder `posterior_reasoning`. The details and instructions can be found in the folder.
- **Evaluation scripts**: Evaluation scripts for both VarDecoder and FieldDecoder can be found in the `training_src` folder.



## Citing us
```
@inproceedings{10.1145/3658644.3670340,
author = {Xie, Danning and Zhang, Zhuo and Jiang, Nan and Xu, Xiangzhe and Tan, Lin and Zhang, Xiangyu},
title = {ReSym: Harnessing LLMs to Recover Variable and Data Structure Symbols from Stripped Binaries},
year = {2024},
isbn = {9798400706363},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3658644.3670340},
doi = {10.1145/3658644.3670340},
abstract = {Decompilation aims to recover a binary executable to the source code form and hence has a wide range of applications in cyber security, such as malware analysis and legacy code hardening. A prominent challenge is to recover variable symbols, including both primitive and complex types such as user-defined data structures, along with their symbol information such as names and types. Existing efforts focus on solving parts of the problem, e.g., recovering only types (without names) or only local variables (without user-defined structures). In this paper, we propose ReSym, a novel hybrid technique that combines Large Language Models (LLMs) and program analysis to recover both names and types for local variables and user-defined data structures. Our method encompasses fine-tuning two LLMs to handle local variables and structures, respectively. To overcome the token limitations inherent in current LLMs, we devise a novel Prolog-based algorithm to aggregate and cross-check results from multiple LLM queries, suppressing uncertainty and hallucinations. Our experiments show that ReSym is effective in recovering variable information and user-defined data structures, substantially outperforming the state-of-the-art methods.},
booktitle = {Proceedings of the 2024 on ACM SIGSAC Conference on Computer and Communications Security},
pages = {4554–4568},
numpages = {15},
keywords = {large language models, program analysis, reverse engineering},
location = {Salt Lake City, UT, USA},
series = {CCS '24}
}
```
