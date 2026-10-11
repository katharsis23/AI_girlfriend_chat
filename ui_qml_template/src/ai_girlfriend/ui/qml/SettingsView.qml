import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Page {
    id: view
    background: Rectangle { color: Theme.background }

    header: TopBar {
        title: qsTr("Settings")
        showBack: true
        onBackClicked: view.StackView.view.pop()
    }

    ColumnLayout {
        y: 16
        width: Math.min(view.width - 32, 640)
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 12

        SettingsRow {
            Layout.fillWidth: true
            glyph: "🎨"
            title: qsTr("Color theme")
            subtitle: settingsBackend.themeInfo(settingsBackend.currentTheme).name
            onClicked: view.StackView.view.push(Qt.resolvedUrl("ThemePicker.qml"))
        }
        SettingsRow {
            Layout.fillWidth: true
            glyph: "💬"
            title: qsTr("Character")
            subtitle: settingsBackend.characterInfo(settingsBackend.currentCharacter).name
            onClicked: view.StackView.view.push(Qt.resolvedUrl("CharacterPicker.qml"))
        }
    }
}
