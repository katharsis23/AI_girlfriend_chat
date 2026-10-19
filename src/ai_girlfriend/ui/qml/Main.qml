import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import App 1.0
import "components"

ApplicationWindow {
    id: win
    visible: true
    width: 480
    height: 760
    minimumWidth: 360
    minimumHeight: 520
    flags: Qt.Window | Qt.FramelessWindowHint
    title: Backends.chat.characterName.length > 0
           ? qsTr("Companion — %1").arg(Backends.chat.characterName)
           : qsTr("Companion")
    color: "transparent"

    Material.theme: ThemeController.isDark ? Material.Dark : Material.Light
    Material.accent: Theme.primary
    Material.primary: Theme.surface
    Material.background: Theme.background
    Material.foreground: Theme.text

    Rectangle {
        id: shell
        anchors.fill: parent
        anchors.margins: 1
        radius: 24
        color: Theme.background
        border.width: 1
        border.color: Qt.alpha(Theme.primary, 0.5)
        clip: true
        Behavior on color { ColorAnimation { duration: Theme.durationMedium } }

        StackView {
            id: stack
            anchors.fill: parent
            initialItem: ChatView { onOpenSettings: stack.push(Qt.resolvedUrl("SettingsView.qml")) }
            pushEnter: Transition { ParallelAnimation { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.durationMedium } NumberAnimation { property: "x"; from: 24; to: 0; duration: Theme.durationMedium; easing.type: Easing.OutCubic } } }
            pushExit: Transition { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.durationShort } }
            popEnter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.durationMedium } }
            popExit: Transition { ParallelAnimation { NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.durationShort } NumberAnimation { property: "x"; from: 0; to: 24; duration: Theme.durationShort } } }
        }
    }

    Rectangle {
        id: snack
        property string message: ""
        z: 10
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 22
        width: Math.min(parent.width - 32, 420)
        height: snackRow.implicitHeight + 20
        radius: 14
        color: Theme.error
        opacity: 0
        visible: opacity > 0
        Behavior on opacity { NumberAnimation { duration: Theme.durationMedium } }
        Accessible.role: Accessible.AlertMessage
        Accessible.name: snack.message
        RowLayout {
            id: snackRow
            anchors.fill: parent; anchors.margins: 10; spacing: 8
            Label { Layout.fillWidth: true; text: snack.message; color: Theme.onError; wrapMode: Text.Wrap; font.pixelSize: Theme.fontSizeM }
            IconButton { glyph: "×"; fg: Theme.onError; accessibleName: qsTr("Dismiss"); implicitWidth: 32; implicitHeight: 32; onClicked: snack.opacity = 0 }
        }
        Timer { id: snackTimer; interval: 5000; onTriggered: snack.opacity = 0 }
        function show(msg) { message = msg; opacity = 1; snackTimer.restart() }
    }
    Connections { target: Backends.chat; function onErrorRaised(message) { snack.show(message) } }
}
