import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: view
    background: Rectangle { color: Theme.background }
    property var chats: []
    header: TopBar { title: qsTr("Your conversations"); subtitle: qsTr("Pick up where you left off"); showBack: true; onBackClicked: view.StackView.view.pop() }
    Connections { target: Backends.chat; function onChatsListed(items) { view.chats = items } }

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 16; spacing: 12
        Label { text: qsTr("RECENT CHATS"); color: Theme.onSurfaceVariant; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.4; Layout.leftMargin: 4 }
        ListView {
            id: list
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true; spacing: 8; model: view.chats; boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            delegate: AbstractButton {
                width: list.width; height: Math.max(82, contentRow.implicitHeight + 22)
                padding: 12; hoverEnabled: true
                Accessible.role: Accessible.ListItem; Accessible.name: modelData.preview
                onClicked: Backends.chat.loadChat(modelData.id)
                background: Rectangle {
                    radius: 17; color: parent.hovered ? Theme.surfaceVariant : Theme.surface
                    border.width: 1; border.color: parent.hovered ? Qt.alpha(Theme.primary, 0.7) : Qt.alpha(Theme.outline, 0.18)
                    Behavior on color { ColorAnimation { duration: 120 } }
                }
                contentItem: RowLayout {
                    id: contentRow; spacing: 12
                    Rectangle {
                        Layout.preferredWidth: 44; Layout.preferredHeight: 44; radius: 15
                        color: Qt.alpha(Theme.primary, 0.14)
                        Text { anchors.centerIn: parent; text: "◌"; color: Theme.primary; font.pixelSize: 26 }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 5
                        Label { Layout.fillWidth: true; text: modelData.preview.length > 0 ? modelData.preview : qsTr("Empty conversation"); elide: Text.ElideRight; color: Theme.onSurface; font.pixelSize: Theme.fontSizeM; font.weight: Font.Medium }
                        Label { Layout.fillWidth: true; text: modelData.updated + "  ·  " + qsTr("%n message(s)", "", modelData.count); elide: Text.ElideRight; color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS }
                    }
                    Label { text: "›"; color: Theme.onSurfaceVariant; font.pixelSize: 26 }
                }
            }
        }
    }
    ColumnLayout {
        anchors.centerIn: parent; width: Math.min(view.width - 64, 360); spacing: 8
        visible: view.chats.length === 0
        Rectangle { Layout.alignment: Qt.AlignHCenter; width: 68; height: 68; radius: 24; color: Theme.surfaceVariant; Text { anchors.centerIn: parent; text: "◷"; color: Theme.primary; font.pixelSize: 34 } }
        Label { Layout.fillWidth: true; text: qsTr("Nothing here yet"); horizontalAlignment: Text.AlignHCenter; color: Theme.onSurface; font.pixelSize: Theme.fontSizeL; font.weight: Font.DemiBold }
        Label { Layout.fillWidth: true; text: qsTr("Your conversations will be saved here, ready whenever you want to return."); horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap; color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeM }
    }
    Component.onCompleted: Backends.chat.listChats(50)
}
