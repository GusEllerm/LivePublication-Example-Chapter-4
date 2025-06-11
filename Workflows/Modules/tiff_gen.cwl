cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python3"]
arguments: [$(inputs.tiff_gen)]

requirements: []

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