import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

// Live-applying theme list with 3-swatch preview (spec §5.4)
Page {
    id: view
    background: Rectangle { color: Theme.background }

    header: TopBar {
        title: qsTr("Color theme")
        showBack: true
        onBackClicked: view.StackView.view.pop()
    }

    ListView {
        id: list
        anchors.fill: parent
        clip: true
        spacing: 12
        topMargin: 16
        bottomMargin: 96
        model: settingsBackend.themes

        delegate: Item {
            id: item
            width: list.width
            height: 88
            readonly property var info: settingsBackend.themeInfo(modelData)
            readonly property bool isActive: settingsBackend.currentTheme === modelData

            AbstractButton {
                id: card
                width: Math.min(list.width - 32, 640)
                height: parent.height
                anchors.horizontalCenter: parent.horizontalCenter
                padding: 16
                hoverEnabled: true
                Accessible.role: Accessible.RadioButton
                Accessible.name: item.info.name
                Accessible.checked: item.isActive
                onClicked: settingsBackend.selectTheme(modelData)

                background: Rectangle {
                    radius: Theme.radius
                    color: Theme.surface
                    border.width: item.isActive ? 2 : 1
                    border.color: item.isActive ? Theme.primary : Theme.surfaceVariant
                    Behavior on border.color { ColorAnimation { duration: 150 } }
                }
                contentItem: RowLayout {
                    spacing: 16
                    Row {
                        spacing: -10
                        Repeater {
                            model: [item.info.primary, item.info.secondary, item.info.background]
                            Rectangle {
                                width: 38; height: 38; radius: 19
                                color: modelData
                                border.width: 2
                                border.color: Theme.outline
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label { text: item.info.name; color: Theme.onSurface; font.pixelSize: Theme.fontSizeM + 1; font.weight: Font.Medium }
                        Label {
                            text: (item.info.dark ? qsTr("Dark") : qsTr("Light"))
                                  + (item.info.custom ? " · " + qsTr("Custom") : "")
                            color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS + 1
                        }
                    }
                    // Edit button for custom themes only.
                    IconButton {
                        visible: item.info.custom
                        glyph: "✎"
                        fg: Theme.onSurfaceVariant
                        accessibleName: qsTr("Edit theme")
                        implicitWidth: 36
                        implicitHeight: 36
                        onClicked: view.StackView.view.push(Qt.resolvedUrl("ThemeEditor.qml"),
                                                            { themeId: modelData })
                    }
                    Rectangle {
                        Layout.preferredWidth: 28; Layout.preferredHeight: 28
                        radius: 14
                        color: Theme.primary
                        opacity: item.isActive ? 1 : 0
                        scale: item.isActive ? 1 : 0.6
                        Behavior on opacity { NumberAnimation { duration: 150 } }
                        Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }
                        Text { anchors.centerIn: parent; text: "✓"; color: Theme.onPrimary; font.pixelSize: 16; font.bold: true }
                    }
                }
            }
        }
    }

    // Floating action button: create a new custom theme.
    Rectangle {
        width: 56; height: 56; radius: 28
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 24
        color: Theme.primary
        Accessible.role: Accessible.Button
        Accessible.name: qsTr("Create theme")
        Text { anchors.centerIn: parent; text: "+"; color: Theme.onPrimary; font.pixelSize: 30; font.bold: true }
        MouseArea {
            anchors.fill: parent
            onClicked: view.StackView.view.push(Qt.resolvedUrl("ThemeEditor.qml"))
        }
    }
}
