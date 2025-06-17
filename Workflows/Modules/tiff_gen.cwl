#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool

label: "Vegetation Index TIFF Generator"
doc: |
  This CWL tool converts a vegetation index matrix (in pickle format)
  into a color-mapped GeoTIFF file. It dynamically loads a TIFF generation
  script (tiff_gen.py) which depends on auxiliary functions from file_handling.py.

baseCommand: ["python3"]
arguments: [$(inputs.tiff_gen)]

requirements:
  InitialWorkDirRequirement:
    listing:
      - $(inputs.tiff_gen)
      - $(inputs.tiff_gen.secondaryFiles[0])
  DockerRequirement:
    dockerPull: gusellerm/veg-index-container:latest  
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