#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool

baseCommand: ["python3"]
arguments: [$(inputs.index_def)]
requirements: 
  InlineJavascriptRequirement: {}

inputs: 
  index_def:
    type: File
    default:
      class: File
      location: Scripts/index_def.py
      secondaryFiles:
        - class: File
          location: Scripts/file_handling.py

  index:
    type: string
    inputBinding:
      position: 1
      prefix: -i

  # TODO: Perhaps changing this to a string input instead of a file[] would enable the scattering behaviour for batch processing. Should test this out

  bands:
    type: File[]
    inputBinding:
        prefix: -b
        separate: true
        position: 2

outputs: 
  index_matrix:
    type: File
    outputBinding:
      glob: "*$(inputs.index)*.pickle"

  all_outputs:
    type: File[]
    outputBinding: 
      glob: "*.pickle"

    
  

