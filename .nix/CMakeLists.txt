cmake_minimum_required(VERSION 3.20)

project(melee-native LANGUAGES C)

include(GNUInstallDirs)

file(GLOB_RECURSE SOURCES "src/melee/**.c" LIST_DIRECTORIES FALSE)
file(GLOB_RECURSE HSD_SOURCES "src/sysdolphin/**.c" LIST_DIRECTORIES FALSE)
set(SOURCES ${SOURCES} ${HSD_SOURCES})

add_compile_definitions(TARGET_PC)

add_compile_definitions(bool=int)

# Keep exclusions exact so unrelated new sources are always checked.
function(exclude_native_source source reason)
    set(path "${CMAKE_CURRENT_SOURCE_DIR}/${source}")
    if(NOT path IN_LIST SOURCES)
        message(FATAL_ERROR "Native exclusion does not select a source: ${source}")
    endif()
    list(REMOVE_ITEM SOURCES "${path}")
    set(SOURCES "${SOURCES}" PARENT_SCOPE)
    list(APPEND NATIVE_EXCLUSIONS "{\"path\": \"${source}\", \"reason\": \"${reason}\"}")
    set(NATIVE_EXCLUSIONS "${NATIVE_EXCLUSIONS}" PARENT_SCOPE)
endfunction()

exclude_native_source(src/melee/db/dberror.c "OSContext register usage")
exclude_native_source(src/melee/gm/gmmain.c "CARDInit")
exclude_native_source(src/melee/lb/lb_0195.c "PADSetSamplingRate")
exclude_native_source(src/melee/lb/lb_01F8.c "Requires dolphin/thp")
exclude_native_source(src/melee/lb/lbcardnew.c "Asynchronous CARD APIs")
exclude_native_source(src/melee/lb/lbmthp.c "Requires dolphin/thp")
exclude_native_source(src/sysdolphin/baselib/debug.c "PPC register usage")
exclude_native_source(src/sysdolphin/baselib/debugconsole_main.c "PPC register usage")
exclude_native_source(src/sysdolphin/baselib/fog.c "GXInitFogAdjTable")
exclude_native_source(src/sysdolphin/baselib/hsd_3915.c "Requires debug font from DOL")
exclude_native_source(src/sysdolphin/baselib/pobj.c "Nontrivial GXSetArray usage")
exclude_native_source(src/sysdolphin/baselib/sislib_font.c "Requires font from DOL")
exclude_native_source(src/sysdolphin/baselib/video.c "VIPadFrameBufferWidth")

add_library(melee STATIC ${SOURCES})

target_include_directories(melee PRIVATE
    $ENV{AURORA_SRC}/include
    src
)

install(TARGETS melee LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}")

# This describes the compile target; CI publishes it only after a successful build.
get_target_property(NATIVE_SOURCES melee SOURCES)
list(TRANSFORM NATIVE_SOURCES REPLACE "^${CMAKE_CURRENT_SOURCE_DIR}/" "")
list(JOIN NATIVE_SOURCES "\",\n        \"" NATIVE_SOURCES_JSON)
list(JOIN NATIVE_EXCLUSIONS ",\n        " NATIVE_EXCLUSIONS_JSON)
math(EXPR NATIVE_POINTER_BITS "8 * ${CMAKE_SIZEOF_VOID_P}")
execute_process(COMMAND "${CMAKE_C_COMPILER}" -dumpmachine
    OUTPUT_VARIABLE NATIVE_TARGET OUTPUT_STRIP_TRAILING_WHITESPACE
    COMMAND_ERROR_IS_FATAL ANY)
file(CONFIGURE OUTPUT native-compile.json CONTENT [=[
{
    "version": 1,
    "scope": ["src/melee", "src/sysdolphin"],
    "compiler": {
        "id": "@CMAKE_C_COMPILER_ID@",
        "version": "@CMAKE_C_COMPILER_VERSION@",
        "target": "@NATIVE_TARGET@",
        "pointer_bits": @NATIVE_POINTER_BITS@
    },
    "sources": [
        "@NATIVE_SOURCES_JSON@"
    ],
    "excluded": [
        @NATIVE_EXCLUSIONS_JSON@
    ]
}
]=] @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/native-compile.json"
    DESTINATION "${CMAKE_INSTALL_DATADIR}/melee")
