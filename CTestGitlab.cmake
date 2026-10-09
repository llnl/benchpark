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

# Submit results to CDash only for Nightly runs.
if ("${TEST_TYPE}" STREQUAL "Nightly")
    ctest_submit(
        PARTS Update Test # 'Configure' and 'Build' not uploaded
        HTTPHEADER "Authorization: Bearer ${_auth_token}"
    )
endif()
