#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool

baseCommand: ["python3"]
arguments: [$(inputs.tiff_gen)]

requirements:
  InitialWorkDirRequirement:
    listing:
      - $(inputs.tiff_gen)
      - $(inputs.tiff_gen.secondaryFiles[0])
  DockerRequirement:
    dockerPull: veg-index-container:v1.0
  ResourceRequirement:
    ramMin: 32000

inputs:
  tiff_gen: 
    type: File
    default:
      class: File
      location: Scripts/tiff_gen.py
      secondaryFiles: 
        - class: File
          location: Scripts/file_handling.py

  index_array:
    type: File
    inputBinding:
      position: 1
      prefix: -i

  color:
    type: string
    inputBinding:
      position: 2
      prefix: -c

outputs:
  tiff:
    type: File
    outputBinding:
      glob: "*.tif"