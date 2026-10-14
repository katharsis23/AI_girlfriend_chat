import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

// A simple in-app image/file browser (task 3).
//
// QML's own FileDialog needs a native platform dialog that is not always
// available; this dialog is built on the read-only `fileBackend` (a Python
// context property) and works everywhere. It lists directories and image files,
// lets the user navigate up/down and type a path, and emits `fileSelected(path)`
// with the chosen absolute file path.
Dialog {
    id: dialog
    signal fileSelected(string path)

    property string currentPath: Backends.filesystem.cwd
    property var entries: []

    title: qsTr("Choose an image")
    modal: true
    anchors.centerIn: parent
    width: Math.min(parent ? parent.width - 48 : 560, 560)
    height: Math.min(parent ? parent.height - 96 : 560, 560)
    padding: 16

    onOpened: refresh(dialog.currentPath)

    function refresh(path) {
        if (Backends.filesystem.setCwd(path)) {
            dialog.currentPath = Backends.filesystem.cwd
            dialog.entries = Backends.filesystem.listDir(Backends.filesystem.cwd)
        }
    }

    background: Rectangle {
        radius: Theme.radius
        color: Theme.surface
        border.width: 1
        border.color: Theme.outline
    }

    contentItem: ColumnLayout {
        spacing: 10

        // Path bar: up button + editable path.
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            IconButton {
                glyph: "↑"
                accessibleName: qsTr("Parent folder")
                implicitWidth: 40; implicitHeight: 40
                onClicked: dialog.refresh(Backends.filesystem.parent(dialog.currentPath))
            }
            TextField {
                id: pathField
                Layout.fillWidth: true
                text: dialog.currentPath
                color: Theme.onSurface
                font.family: "monospace"
                selectByMouse: true
                onAccepted: dialog.refresh(text)
            }
            IconButton {
                glyph: "⌂"
                accessibleName: qsTr("Home folder")
                implicitWidth: 40; implicitHeight: 40
                onClicked: dialog.refresh(Backends.filesystem.home)
            }
        }

        // Entry list.
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 12
            color: Theme.surfaceVariant
            border.width: 1
            border.color: Theme.outline

            ListView {
                id: list
                anchors.fill: parent
                anchors.margins: 6
                clip: true
                model: dialog.entries
                spacing: 2

                delegate: AbstractButton {
                    width: list.width
                    height: 44
                    padding: 8
                    Accessible.role: Accessible.ListItem
                    Accessible.name: modelData.name
                    onClicked: {
                        if (modelData.isDir) {
                            dialog.refresh(modelData.path)
                        } else {
                            dialog.fileSelected(modelData.path)
                            dialog.close()
                        }
                    }
                    background: Rectangle {
                        radius: 8
                        color: parent.hovered ? Theme.primary : "transparent"
                        opacity: parent.hovered ? 0.16 : 1
                    }
                    contentItem: RowLayout {
                        spacing: 10
                        Text {
                            text: modelData.isDir ? "📁" : "🖼️"
                            color: Theme.onSurface
                            font.pixelSize: Theme.fontSizeM
                        }
                        Label {
                            Layout.fillWidth: true
                            text: modelData.name
                            elide: Text.ElideMiddle
                            color: Theme.onSurface
                            font.pixelSize: Theme.fontSizeM
                        }
                    }
                }

                Label {
                    anchors.centerIn: parent
                    visible: dialog.entries.length === 0
                    text: qsTr("No images here")
                    color: Theme.onSurfaceVariant
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button {
                text: qsTr("Cancel")
                contentItem: Text {
                    text: parent.text
                    color: Theme.onSurface
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    opacity: parent.enabled ? 1.0 : 0.5
                }
                onClicked: dialog.close()
            }
        }
    }
}
