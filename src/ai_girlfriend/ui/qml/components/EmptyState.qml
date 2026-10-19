import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Item {
    id: root
    property string greeting: ""
    property string expression: "neutral"
    property string source: ""
    property string emoji: ""
    property bool showPortrait: true
    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - 44, 360)
        spacing: 12
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            width: 164; height: 164; radius: 58
            color: Qt.alpha(Theme.primary, 0.08)
            border.width: 1; border.color: Qt.alpha(Theme.primary, 0.18)
            visible: root.showPortrait
            Portrait {
                anchors.centerIn: parent
                width: 140; height: 140
                expression: root.expression; source: root.source; emoji: root.emoji
            }
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            text: root.greeting
            color: Theme.text
            font.pixelSize: 22
            font.weight: Font.DemiBold
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            text: qsTr("A quiet little corner of your day. Say hello and see where the conversation goes.")
            color: Theme.onSurfaceVariant
            font.pixelSize: Theme.fontSizeM
            lineHeight: 1.25
        }
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 5
            radius: 12; color: Theme.surfaceVariant
            implicitWidth: hint.implicitWidth + 22; implicitHeight: 30
            Row {
                id: hint; anchors.centerIn: parent; spacing: 7
                Text { text: "↳"; color: Theme.primary; font.pixelSize: 15 }
                Text { text: qsTr("Start with a message below"); color: Theme.onSurfaceVariant; font.pixelSize: 11 }
            }
        }
    }
}
