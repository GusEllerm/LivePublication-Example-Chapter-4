#!/usr/bin/env cwl-runner

cwlVersion: v1.0

requirements:
  MultipleInputFeatureRequirement: {}

class: Workflow
inputs:
  index:
    type: string
  bands:
    type: File[]
  color:
    type: string

outputs:
  tiff:
    type: File
    outputSource: tiff_gen/tiff
  all_outputs:
    type: File[]
    outputSource: index_def/all_outputs


steps:
  index_def:
    run: Modules/index_def.cwl
    in:
      index: index
      bands: bands
    out: [index_matrix, all_outputs]

  tiff_gen:
    run: Modules/tiff_gen.cwl
    in:
      index_array: index_def/index_matrix
      color: color
    out: [tiff]
