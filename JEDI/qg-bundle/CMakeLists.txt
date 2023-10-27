# (C) Copyright 2022 UCAR
#

cmake_minimum_required( VERSION 3.12 FATAL_ERROR )

find_package( ecbuild 3.6 REQUIRED HINTS ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/../ecbuild)

project( qg-bundle VERSION 5.0.0 LANGUAGES C CXX Fortran )

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

include( ecbuild_bundle )

# Default release mode
set( ECBUILD_DEFAULT_BUILD_TYPE Release )

# Enable OpenMP and MPI
set( ENABLE_MPI ON CACHE BOOL "Compile with MPI" )
set( ENABLE_OMP ON CACHE BOOL "Compile with OpenMP" )

# Define bundle
ecbuild_bundle_initialize()

# add the automatically determined parts of the RPATH
# which point to directories outside the build tree to the install RPATH
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH OFF)

# when building, already use the install RPATH
set(CMAKE_BUILD_WITH_INSTALL_RPATH OFF)

# Use external jedi-cmake or build in bundle
if(DEFINED ENV{jedi_cmake_ROOT})
  include( $ENV{jedi_cmake_ROOT}/share/jedicmake/Functions/git_functions.cmake )
else()
  ecbuild_bundle( PROJECT jedicmake GIT "https://github.com/jcsda/jedi-cmake.git" BRANCH develop UPDATE RECURSIVE )
  include( jedicmake/cmake/Functions/git_functions.cmake )
endif()

ecbuild_bundle( PROJECT oops     GIT "https://github.com/jcsda/oops.git"        BRANCH develop UPDATE )
ecbuild_bundle( PROJECT ioda     GIT "https://github.com/jcsda/ioda.git"        BRANCH develop UPDATE )
ecbuild_bundle( PROJECT ufo      GIT "https://github.com/jcsda/ufo.git"         BRANCH develop UPDATE )

ecbuild_bundle_finalize()

