set(CTEST_SOURCE_DIRECTORY "${CMAKE_CURRENT_LIST_DIR}")
set(CTEST_BINARY_DIRECTORY "${CMAKE_CURRENT_LIST_DIR}")
set(CTEST_OUTPUT_ON_FAILURE ON)
set(CTEST_CMAKE_GENERATOR "Unix Makefiles")

set(CTEST_UPDATE_COMMAND "git")
set(CTEST_UPDATE_VERSION_ONLY 1)

set(CTEST_SITE ${SITE})
set(CTEST_BUILD_NAME ${BUILD_NAME})

# Separate CTest dashboards for Nightly and non-Nightly testing.
if ("${TEST_TYPE}" STREQUAL "Nightly")
    ctest_start("Nightly" GROUP "${DASHBOARD_NAME}")
else()
    ctest_start("Continuous" GROUP "${DASHBOARD_NAME}")
endif()

ctest_update()
ctest_configure()
ctest_test(INCLUDE "Gitlab")

if(DEFINED TEST_RUNTIME_SECONDS AND NOT "${TEST_RUNTIME_SECONDS}" STREQUAL "")
    file(READ "${CTEST_BINARY_DIRECTORY}/Testing/TAG" _tag_file)
    string(REGEX MATCH "^[^\n]+" _tag "${_tag_file}")
    set(_test_xml "${CTEST_BINARY_DIRECTORY}/Testing/${_tag}/Test.xml")

    if(EXISTS "${_test_xml}")
        file(READ "${_test_xml}" _xml)
        string(REGEX REPLACE
            "<NamedMeasurement type=\"numeric/double\" name=\"Execution Time\">[ \t\r\n]*<Value>[^<]+</Value>"
            "<NamedMeasurement type=\"numeric/double\" name=\"Execution Time\">\n\t\t\t\t\t<Value>${TEST_RUNTIME_SECONDS}</Value>"
            _xml
            "${_xml}"
        )
        file(WRITE "${_test_xml}" "${_xml}")
    endif()
endif()

# Submit results to CDash only for Nightly runs.
if ("${TEST_TYPE}" STREQUAL "Nightly")
    ctest_submit(
        PARTS Update Test # 'Configure' and 'Build' not uploaded
        HTTPHEADER "Authorization: Bearer ${_auth_token}"
    )
endif()
