import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

// Character cards: thumbnail, name, personality blurb, check on the active one (spec §6.3)
Page {
    id: view
    background: Rectangle { color: Theme.background }

    header: TopBar {
        title: qsTr("Character")
        showBack: true
        onBackClicked: view.StackView.view.pop()
    }

    ListView {
        id: list
        anchors.fill: parent
        clip: true
        spacing: 12
        topMargin: 16
        bottomMargin: 16
        model: Backends.settings.characters

        delegate: Item {
            id: item
            width: list.width
            height: 112
            readonly property var info: Backends.settings.characterInfo(modelData)
            readonly property bool isActive: Backends.settings.currentCharacter === modelData

            // The whole card is a single button (selects the character). The
            // edit affordance is a *sibling* overlay (see below) so its click
            // is never swallowed by this button's press/hover handling.
            AbstractButton {
                id: card
                width: Math.min(list.width - 32, 640)
                height: parent.height
                anchors.horizontalCenter: parent.horizontalCenter
                padding: 16
                hoverEnabled: true
                enabled: !Backends.settings.busy
                Accessible.role: Accessible.RadioButton
                Accessible.name: item.info.name
                Accessible.description: item.info.personality
                Accessible.checked: item.isActive
                onClicked: Backends.settings.selectCharacter(modelData)

                background: Rectangle {
                    radius: Theme.radius
                    color: Theme.surface
                    border.width: item.isActive ? 2 : 1
                    border.color: item.isActive ? Theme.primary : Theme.surfaceVariant
                    Behavior on border.color { ColorAnimation { duration: 150 } }
                }
                contentItem: RowLayout {
                    spacing: 16
                    Portrait {
                        Layout.preferredWidth: 72
                        Layout.preferredHeight: 72
                        expression: item.info.expression
                        source: item.info.thumb
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Label { text: item.info.name; color: Theme.onSurface; font.pixelSize: Theme.fontSizeM + 2; font.weight: Font.Medium }
                        Label {
                            Layout.fillWidth: true
                            text: item.info.personality
                            wrapMode: Text.Wrap
                            maximumLineCount: 3
                            elide: Text.ElideRight
                            color: Theme.onSurfaceVariant
                            font.pixelSize: Theme.fontSizeS + 1
                        }
                    }
                    // Reserve room for the overlaid edit + check controls.
                    Item { Layout.preferredWidth: 76; Layout.preferredHeight: 1 }
                }
            }

            // Edit overlay, lifted above the card so clicks always land here.
            IconButton {
                id: editBtn
                z: 2
                glyph: "✎"
                fg: Theme.onSurfaceVariant
                enabled: !Backends.settings.busy
                accessibleName: qsTr("Edit character")
                implicitWidth: 40
                implicitHeight: 40
                anchors.right: card.right
                anchors.rightMargin: 56
                anchors.verticalCenter: card.verticalCenter
                onClicked: view.StackView.view.push(Qt.resolvedUrl("CharacterEditor.qml"),
                                                    { characterId: modelData })
            }

            // Active check badge (non-interactive overlay).
            Rectangle {
                z: 2
                width: 28; height: 28; radius: 14
                color: Theme.primary
                opacity: item.isActive ? 1 : 0
                anchors.right: card.right
                anchors.rightMargin: 16
                anchors.verticalCenter: card.verticalCenter
                Behavior on opacity { NumberAnimation { duration: 150 } }
                Text { anchors.centerIn: parent; text: "✓"; color: Theme.onPrimary; font.pixelSize: 16; font.bold: true }
            }
        }
    }

    // loading state while the pipeline is rebuilt (spec §6.3)
    Rectangle {
        anchors.fill: parent
        color: Theme.background
        opacity: Backends.settings.busy ? 0.72 : 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: 150 } }
        MouseArea { anchors.fill: parent }   // swallow input
        BusyIndicator { anchors.centerIn: parent; running: parent.visible }
    }

    // Floating action button: add a new character.
    Rectangle {
        width: 56; height: 56; radius: 28
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 24
        z: 5
        color: Theme.primary
        Accessible.role: Accessible.Button
        Accessible.name: qsTr("Add character")
        Text { anchors.centerIn: parent; text: "+"; color: Theme.onPrimary; font.pixelSize: 30; font.bold: true }
        MouseArea {
            anchors.fill: parent
            enabled: !Backends.settings.busy
            onClicked: view.StackView.view.push(Qt.resolvedUrl("CharacterEditor.qml"))
        }
    }
}
