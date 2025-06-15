#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool

baseCommand: ["python3"]
arguments: [$(inputs.index_def)]

requirements:
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - $(inputs.index_def)
      - $(inputs.index_def.secondaryFiles[0])  # Ensuring file_handling.py is staged
  DockerRequirement:
    dockerPull: gusellerm/veg-index-container:latest  # Docker image for the workflow
  ResourceRequirement:
    ramMin: 32000  # Min RAM to execute the task

inputs:
  index_def:
    type: File
    default:
      class: File
      location: Scripts/index_def.py  # Path to index_def.py
      secondaryFiles:
        - class: File
          location: Scripts/file_handling.py  # Path to file_handling.py

  index:
    type: string
    inputBinding:
      position: 1
      prefix: -i  # Binding position for 'index' input

  bands:
    type: File[]
    inputBinding:
      prefix: -b  # Binding prefix for 'bands'
      separate: true
      position: 2  # Position for bands

outputs:
  index_matrix:
    type: File
    outputBinding:
      glob: "*$(inputs.index)*.pickle"  # Glob pattern to capture the output pickle file

  all_outputs:
    type: File[]
    outputBinding: 
      glob: "*.pickle"  # Glob pattern to capture all pickle files