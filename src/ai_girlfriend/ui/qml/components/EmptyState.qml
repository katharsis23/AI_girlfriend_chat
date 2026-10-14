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
        width: Math.min(parent.width - 48, 420)
        spacing: 16

        Portrait {
            visible: root.showPortrait
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 140
            Layout.preferredHeight: 140
            expression: root.expression
            source: root.source
            emoji: root.emoji
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            text: root.greeting
            color: Theme.text
            font.pixelSize: Theme.fontSizeL
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            text: qsTr("Type a message below to start the conversation.")
            color: Theme.onSurfaceVariant
            font.pixelSize: Theme.fontSizeM
        }
    }
}
