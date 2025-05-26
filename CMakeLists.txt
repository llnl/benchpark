cmake_minimum_required(VERSION 3.10)
project(PythonTestProject LANGUAGES NONE)
ENABLE_TESTING()
INCLUDE(CTest)
find_package(Python3 REQUIRED)

add_test(NAME Gitlab
        COMMAND ${CMAKE_COMMAND} -E $ENV{EXIT_CODE})
