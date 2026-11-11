# A development package imports a library its dependencies did not install

Symptom: installing a development package succeeds, then `find_package(... REQUIRED)` fails because an imported target references a missing library, or generating a consumer fails because an exported include directory is absent.
The package's own build can still pass: its build dependencies and staging tree contain files a clean consumer never receives.

## Working recipe

1. Compare the signed published package and its source with the newest authored recipe before editing.
   Read the real installed Config.cmake, Targets.cmake and configuration-specific target files.
   Map every imported library, header directory and linker symlink to its binary package.
   A runtime dependency generated from ELF linkage does not supply a sibling's development headers or unversioned linker symlink.
2. Start a clean Debian testing container, pinned by amd64 digest, with the edition's signed repository, deb-multimedia and the edition's pins as [the repository reference](repository.md) describes.
   Mount the HTTPS-only apt helper and CA bundle as required by the build tools, run the helper first, and set `--ulimit core=0`.
   Install build tools and only the development package under investigation as the explicit stereo root:

   ```sh
   sh /run/https-only-apt.sh
   export DEBIAN_FRONTEND=noninteractive
   apt-get -y -o APT::Update::Error-Mode=any update
   apt-cache policy libstereo-layer-dev libstereo-av-dev libstereo-dibr-dev libstereo-policy-dev
   apt-get -y --no-install-recommends install cmake g++ make libstereo-layer-dev
   dpkg-query -W 'libstereo-*'
   ```

   Keep the candidate origins and installed package list.
   Do not preinstall the sibling development packages: that masks the defect.
3. As an unprivileged container user, configure and build a consumer using the installed package, outside its library's build tree.
   These are three functional CMake lines plus the minimum version and project declarations:

   ```cmake
   cmake_minimum_required(VERSION 3.25)
   project(consumer LANGUAGES CXX)
   find_package(StereoLayer REQUIRED)
   add_executable(consumer main.cpp)
   target_link_libraries(consumer PRIVATE Stereo::Layer)
   ```

   A small main must call an installed library symbol; an empty main does not prove linking.
   For example, this headless consumer checks the dimensions and contents of both native eye images:

   ```cpp
   #include <picture.h>

   int main()
   {
       QImage packed(4, 1, QImage::Format_RGB32);
       packed.setPixelColor(0, 0, Qt::red);
       packed.setPixelColor(1, 0, Qt::red);
       packed.setPixelColor(2, 0, Qt::blue);
       packed.setPixelColor(3, 0, Qt::blue);
       auto p = Stereo::Picture::fromPackedImage(packed, Stereo::Picture::Layout::SideBySide, Stereo::Picture::EyeOrder::LeftFirst);
       if (p.left.size() != QSize(2, 1) || p.right.size() != QSize(2, 1))
           return 1;
       return p.left.pixelColor(0, 0) != QColor(Qt::red) || p.right.pixelColor(0, 0) != QColor(Qt::blue);
   }
   ```

   ```sh
   cmake -S consumer -B consumer-build
   cmake --build consumer-build --parallel 4
   ./consumer-build/consumer
   ```

   Retain the original failure and its exit code before changing packaging.
   Also link consumers through the sibling targets if they are part of the same installed export, so missing header directories cannot escape the check.
4. Add the required sibling development packages to the owning development package's **Depends**.
   Use the matching binary version for a cohort built together whose export names exact versioned libraries.
   Locate the authoritative control file: a source generator may copy debian/ from the library repository while an older recipe remains in the build repository.
   Bump the Debian revision for a packaging-only change and build the whole cohort from one source descriptor.
5. Expose the rebuilt packages through a disposable local apt repository with the edition Origin, then simulate **only the development root**, for example `apt-get -s --no-install-recommends install libstereo-layer-dev=VERSION`.
   Read every Inst line and confirm the new development root, sibling development packages and matching runtimes are selected at the candidate version; require no Remv lines.
   Install that same request into the original failing container and rerun the unchanged consumer in a new build directory.
   Keep configure, build and execution exit codes.
   Ordinary local test packages still need the edition's Lean Code preparation and release qualification before publication.
6. Keep a package test whose Depends names the development root and build tools explicitly.
   Using `Depends: @` installs every binary from the source and can hide missing sibling dependencies.

## The stereo-layer case

Found by comparing the published 1.17.1-1+lc1 binaries and generated exports with the 1.17.3-1 authored packaging.
The export imports Stereo::Layer, Stereo::Av, Stereo::Dibr and Stereo::Policy together.
Their development payloads belong to libstereo-layer-dev, libstereo-av-dev, libstereo-dibr-dev and libstereo-policy-dev respectively.
Policy-dev was already required; av-dev and dibr-dev were missing.
The clean configure failed because Stereo::Av referenced the absent libstereo-av.so.1.17.1.
The Dibr runtime arrived through layer1, but its development headers and linker symlink did not.

The fix adds exact-version av-dev and dibr-dev Depends and advances the Debian revision to 1.17.3-2.
The installed consumer then configures, links and runs with the existing config template.
All eight runtime and development packages are selected automatically by the single layer-dev request.

These siblings share one CMake export and provide pkg-config files, not standalone CMake package configs.
Do not invent find_dependency calls for them or make their targets optional.
For an actual external CMake package dependency, [CMakeFindDependencyMacro](https://cmake.org/cmake/help/latest/module/CMakeFindDependencyMacro.html) provides dependency discovery and propagates failure to the caller.
The [CMake importing and exporting guide](https://cmake.org/cmake/help/latest/guide/importing-exporting/index.html) describes the exported locations and usage requirements a consumer needs.
