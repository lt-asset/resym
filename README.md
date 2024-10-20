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




## Citing us
```
@article{xie2024resym,
  title={ReSym: Harnessing LLMs to Recover Variable and Data Structure Symbols from Stripped Binaries},
  author={Xie, Danning and Zhang, Zhuo and Jiang, Nan and Xu, Xiangzhe and Tan, Lin and Zhang, Xiangyu},
  booktitle={Proceedings of the 2024 ACM SIGSAC Conference on Computer and Communications Security},
  year={2024}
}
```
