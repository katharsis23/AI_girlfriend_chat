import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: view
    background: Rectangle { color: Theme.background }
    header: TopBar { title: qsTr("Personalize"); subtitle: qsTr("Make this space yours"); showBack: true; onBackClicked: view.StackView.view.pop() }

    Flickable {
        anchors.fill: parent; contentWidth: width; contentHeight: content.implicitHeight + 36
        clip: true; boundsBehavior: Flickable.StopAtBounds
        ColumnLayout {
            id: content
            width: Math.min(parent.width - 32, 560); anchors.horizontalCenter: parent.horizontalCenter
            y: 16; spacing: 18
            Label { text: qsTr("YOUR COMPANION"); color: Theme.onSurfaceVariant; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.5; Layout.leftMargin: 4 }
            SettingsRow {
                Layout.fillWidth: true; glyph: "♡"; title: qsTr("Characters"); subtitle: Backends.settings.characterInfo(Backends.settings.currentCharacter).name + qsTr(" · choose or create a persona")
                onClicked: view.StackView.view.push(Qt.resolvedUrl("CharacterPicker.qml"))
            }
            SettingsRow {
                Layout.fillWidth: true; glyph: "✧"; title: qsTr("Appearance"); subtitle: Backends.settings.themeInfo(Backends.settings.currentTheme).name + qsTr(" · colors and mood")
                onClicked: view.StackView.view.push(Qt.resolvedUrl("ThemePicker.qml"))
            }
            Label { text: qsTr("YOUR SPACE"); color: Theme.onSurfaceVariant; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.5; Layout.leftMargin: 4; Layout.topMargin: 4 }
            SettingsRow {
                Layout.fillWidth: true; glyph: "◷"; title: qsTr("Conversation history"); subtitle: qsTr("Return to a moment from an earlier chat")
                onClicked: view.StackView.view.push(Qt.resolvedUrl("ChatHistoryView.qml"))
            }
            Rectangle {
                Layout.fillWidth: true; implicitHeight: 92; radius: 18
                color: Qt.alpha(Theme.primary, 0.09); border.width: 1; border.color: Qt.alpha(Theme.primary, 0.18)
                RowLayout {
                    anchors.fill: parent; anchors.margins: 14; spacing: 12
                    Text { text: "✦"; color: Theme.primary; font.pixelSize: 25 }
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 3
                        Label { text: qsTr("A little space just for you"); color: Theme.onSurface; font.pixelSize: Theme.fontSizeM; font.weight: Font.Medium }
                        Label { Layout.fillWidth: true; text: qsTr("Create a character or theme to give your chats a different feel."); wrapMode: Text.Wrap; color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS }
                    }
                }
            }
        }
    }
}
