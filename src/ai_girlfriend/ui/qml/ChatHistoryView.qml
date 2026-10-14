import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

// Browse stored conversations and reopen one (frontend task 5).
// Backed by the pipeline's read-only history API (`list_chats` / `get_messages`).
Page {
    id: view
    background: Rectangle { color: Theme.background }

    // In-progress list of conversation summaries.
    property var chats: []

    header: TopBar {
        title: qsTr("Chat history")
        showBack: true
        onBackClicked: view.StackView.view.pop()
    }

    Connections {
        target: Backends.chat
        function onChatsListed(items) { view.chats = items }
    }

    ListView {
        id: list
        anchors.fill: parent
        clip: true
        spacing: 8
        topMargin: 16
        bottomMargin: 16
        model: view.chats

        delegate: AbstractButton {
            width: Math.min(list.width - 32, 720)
            anchors.horizontalCenter: parent.horizontalCenter
            height: Math.max(72, contentRow.implicitHeight + 24)
            padding: 12
            hoverEnabled: true
            Accessible.role: Accessible.ListItem
            Accessible.name: modelData.preview
            onClicked: Backends.chat.loadChat(modelData.id)

            background: Rectangle {
                radius: Theme.radius
                color: Theme.surface
                border.width: 1
                border.color: parent.hovered ? Theme.primary : Theme.surfaceVariant
                Behavior on border.color { ColorAnimation { duration: 150 } }
            }

            contentItem: RowLayout {
                id: contentRow
                spacing: 12

                Rectangle {
                    Layout.preferredWidth: 44
                    Layout.preferredHeight: 44
                    radius: 22
                    color: Theme.primary
                    Text {
                        anchors.centerIn: parent
                        text: "💬"
                        font.pixelSize: Theme.fontSizeL
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        Layout.fillWidth: true
                        text: modelData.preview.length > 0 ? modelData.preview : qsTr("(empty)")
                        elide: Text.ElideRight
                        color: Theme.onSurface
                        font.pixelSize: Theme.fontSizeM
                    }
                    Label {
                        Layout.fillWidth: true
                        text: modelData.updated + " · " + qsTr("%n message(s)", "", modelData.count)
                        elide: Text.ElideRight
                        color: Theme.onSurfaceVariant
                        font.pixelSize: Theme.fontSizeS
                    }
                }
                Label {
                    text: "›"
                    color: Theme.onSurfaceVariant
                    font.pixelSize: Theme.fontSizeXL
                }
            }
        }
    }

    // Empty state.
    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(view.width - 64, 420)
        spacing: 8
        visible: view.chats.length === 0
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: "🕘"
            font.pixelSize: 48
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: qsTr("No previous conversations yet")
            color: Theme.onSurface
            font.pixelSize: Theme.fontSizeM
        }
        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            text: qsTr("Start chatting and your history will appear here.")
            color: Theme.onSurfaceVariant
            font.pixelSize: Theme.fontSizeS + 1
        }
    }

    Component.onCompleted: Backends.chat.listChats(50)
}
