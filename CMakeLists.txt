cmake_minimum_required(VERSION 3.10)
project(PythonTestProject LANGUAGES NONE)
ENABLE_TESTING()
INCLUDE(CTest)
find_package(Python3 REQUIRED)

add_test(NAME Gitlab
        COMMAND bash -c "./bin/benchpark analyze --workspace-dir wkp/dane/kripke/workspace --ctest-emit &&
        exec ${CMAKE_COMMAND} -E \"$EXIT_CODE\""
)

