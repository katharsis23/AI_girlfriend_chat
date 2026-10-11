{
  pkgs ? import <nixpkgs> { },
}:

let
  # Runtime libraries required by the Qt xcb platform plugin
  # (libqxcb.so) and its dependency libxcb-cursor. Without these in
  # LD_LIBRARY_PATH the plugin fails to load under NixOS.
  runtimeLibs = with pkgs; [
    # C / stdlib runtime needed by the pip-installed PySide6
    stdenv.cc.cc.lib
    zlib
    zstd
    glib
    fontconfig
    freetype
    # OpenGL / rendering
    libGL
    libglvnd
    libdrm
    mesa
    # X11 stack
    libx11
    libxext
    libxrender
    libxi
    libxtst
    libxcb
    libxcb-util
    libxcb-image
    libxcb-keysyms
    libxcb-render-util
    libxcb-wm # provides xcb-icccm + xcb-ewmh
    libxcb-cursor
    # Keyboard / windowing / misc
    libxkbcommon
    wayland
    libinput
    dbus.lib
    krb5
  ];
in
pkgs.mkShell {
  buildInputs =
    with pkgs;
    [
      python313
      poetry

      qt6.qtbase
      qt6.wrapQtAppsHook
    ]
    ++ runtimeLibs;

  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath runtimeLibs}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

    # Prefer PySide6's own bundled Qt plugins/QML modules, since the app is
    # run with the pip-installed Qt 6.12 rather than the system qtbase.
    # Resolve them relative to the active virtualenv; fall back to the
    # system qtbase if PySide6 is not installed yet.
    PYSIDE_DIR="''${VIRTUAL_ENV:-$(dirname "$(dirname "$(command -v python || echo /usr/bin/python)")")}"
    if [ -d "$PYSIDE_DIR/lib/python"*"/site-packages/PySide6/Qt/plugins" ]; then
      export QT_PLUGIN_PATH="$(echo "$PYSIDE_DIR"/lib/python*/site-packages/PySide6/Qt/plugins)"
      export QML2_IMPORT_PATH="$(echo "$PYSIDE_DIR"/lib/python*/site-packages/PySide6/Qt/qml)"
    else
    export QT_PLUGIN_PATH="${pkgs.qt6.qtbase.out}/lib/qt-6/plugins"
    export QML2_IMPORT_PATH="${pkgs.qt6.qtbase.out}/lib/qt-6/qml"
    fi

    export QT_QPA_PLATFORM="''${QT_QPA_PLATFORM:-xcb}"

    export POETRY_PYTHON="${pkgs.python313}/bin/python3"

    echo "Python virtual environment ready on NixOS!"
  '';
}
