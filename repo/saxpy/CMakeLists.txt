# Copyright 2023 Lawrence Livermore National Security, LLC and other
# Benchpark Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.23)

option(USE_OPNEMP "Use OpenMP" OFF)
option(USE_CUDA "Use CUDA" OFF)
option(USE_HIP "Use HIP" OFF)
option(USE_CALIPER "Enable Caliper" FALSE)

if(USE_CUDA)
  project(saxpy VERSION 1.0.0 LANGUAGES CXX CUDA)
else()
  project(saxpy VERSION 1.0.0 LANGUAGES CXX)
endif()

set(SOURCES saxpy.cc)
set(SAXPY_DEPENDENCIES )

add_executable(${PROJECT_NAME} ${SOURCES})

find_package(MPI REQUIRED)
list(APPEND SAXPY_DEPENDENCIES
  MPI::MPI_CXX)

if(USE_OPENMP)
    target_compile_options(${PROJECT_NAME} PRIVATE -DUSE_OPENMP)
    find_package(OpenMP REQUIRED)
    list(APPEND SAXPY_DEPENDENCIES
      OpenMP::OpenMP_CXX)
endif()

if(USE_HIP)
    include_directories(${ROCM_PATH}/include)
    target_compile_options(${PROJECT_NAME} PRIVATE -x hip -DUSE_HIP --offload-arch=${ROCM_ARCH})
    list(APPEND SAXPY_DEPENDENCIES
      "-L${ROCM_PATH}/lib -lamdhip64")
endif()

if(USE_CUDA)
    set_source_files_properties(saxpy.cc PROPERTIES LANGUAGE "CUDA")
    set(CMAKE_CUDA_STANDARD_REQUIRED TRUE)
    set(CMAKE_CXX_STANDARD_REQUIRED TRUE)
    set(CMAKE_CXX_EXTENSIONS OFF)
    set(CMAKE_CUDA_FLAGS "-Xcompiler -DUSE_CUDA")
    set_target_properties(${PROJECT_NAME} PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
endif()

if (USE_CALIPER)
  find_package(caliper REQUIRED)
  list(APPEND SAXPY_DEPENDENCIES 
    caliper)
  find_package(adiak REQUIRED)
  list(APPEND SAXPY_DEPENDENCIES
    adiak::adiak)
  target_compile_options(${PROJECT_NAME} PRIVATE -DUSE_CALIPER)
endif()

configure_file(
  "${CMAKE_SOURCE_DIR}/config.hh.in"
  "${CMAKE_CURRENT_SOURCE_DIR}/config.hh"
)

target_link_libraries(${PROJECT_NAME} PRIVATE ${SAXPY_DEPENDENCIES})

install(TARGETS ${PROJECT_NAME}
        DESTINATION bin
)
