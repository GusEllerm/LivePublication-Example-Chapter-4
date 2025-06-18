#!/usr/bin/env cwl-runner

cwlVersion: v1.0

requirements:
  MultipleInputFeatureRequirement: {}

class: Workflow

label: "Vegetation Index Workflow"
doc: |
  A CWL workflow for computing a vegetation index (e.g., NDVI, GNDVI)
  from Sentinel-2 band inputs and generating a color-mapped GeoTIFF.
inputs:
  index:
    type: string
    label: "Vegetation Index"
    doc: The name of the vegetation index to compute (e.g., NDVI, GNDVI)

  bands:
    type: File[]
    label: "Spectral Bands"
    doc: A list of spectral band raster files (e.g., B03, B08) for the index calculation.

  color:
    type: string
    label: "Color Map"
    doc: The name of the matplotlib-compatible color map for the output TIFF.


outputs:
  tiff:
    type: File
    outputSource: tiff_gen/tiff
    label: "Color-Mapped GeoTIFF"
    doc: The final TIFF image output with the vegetation index and color map applied.

  all_outputs:
    type: File[]
    outputSource: index_def/all_outputs
    label: "All Output Pickle Files"
    doc: All intermediate and final pickle outputs from the index computation.



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
