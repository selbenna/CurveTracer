cmake_minimum_required(VERSION 2.8.9)

project(CurveTracer)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/CurveTracer")
set(EXTENSION_CATEGORY "Informatics")
set(EXTENSION_CONTRIBUTORS "Sarah Elbanna, Junichi Tokuda (BWH)")
set(EXTENSION_DESCRIPTION "This module traces a curve and lists structures intersecting with it.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/CurveTracer.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/CurveTracer/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(CurveTracer)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
