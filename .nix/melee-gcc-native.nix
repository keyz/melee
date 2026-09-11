{
  lib,
  applyPatches,
  stdenv,
  cmake,
  aurora-src,
}:
stdenv.mkDerivation {
  name = "melee-gcc-native";

  src = lib.fileset.toSource {
    root = ../.;
    fileset = lib.fileset.unions [
      ../extern/dolphin/include/dolphin/thp
      ../src/sysdolphin
      ../src/melee
      ../src/Runtime
      ../src/placeholder.h
      ../src/m2c_macros.h
    ];
  };

  postPatch = ''
    cp ${./CMakeLists.txt} CMakeLists.txt
  '';

  nativeBuildInputs = [
    cmake
  ];

  makeFlags = [ "-k" ];

  env.AURORA_SRC = applyPatches {
    name = "aurora-native-support";
    src = aurora-src;
    patches = [ ./aurora-card-format.patch ];
  };

  __structuredAttrs = true;
}
