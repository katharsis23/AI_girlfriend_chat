import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    property string role: "assistant"
    property string text: ""
    readonly property bool isUser: role === "user"
    readonly property real padH: 15
    readonly property real padV: 11
    readonly property real maxBubble: Math.min(width * 0.82, 520)
    width: ListView.view ? ListView.view.width : 400
    height: bubble.height + 10
    Accessible.role: Accessible.StaticText
    Accessible.name: (isUser ? qsTr("You") : qsTr("Companion")) + ": " + text

    TextMetrics { id: metrics; font: body.font; text: root.text; elide: Text.ElideNone }
    Rectangle {
        id: bubble
        anchors.left: root.isUser ? undefined : parent.left
        anchors.right: root.isUser ? parent.right : undefined
        anchors.leftMargin: 4; anchors.rightMargin: 4
        width: Math.min(root.maxBubble, Math.max(64, Math.min(metrics.boundingRect.width + 2 * root.padH, root.maxBubble)))
        height: body.contentHeight + 2 * root.padV
        radius: 17
        color: root.isUser ? Theme.primary : Theme.surfaceVariant
        border.width: root.isUser ? 0 : 1
        border.color: Qt.alpha(Theme.outline, 0.14)
        TextEdit {
            id: body
            x: root.padH; y: root.padV
            width: bubble.width - 2 * root.padH
            text: root.text; readOnly: true; selectByMouse: true
            wrapMode: TextEdit.Wrap; textFormat: TextEdit.PlainText
            color: root.isUser ? Theme.onPrimary : Theme.onSurface
            selectionColor: Theme.primary; selectedTextColor: Theme.onPrimary
            font.pixelSize: Theme.fontSizeM
            font.family: "Inter, Noto Sans, sans-serif"
        }
    }
    opacity: 0
    transform: Translate { id: slide; y: 8 }
    Component.onCompleted: enter.start()
    ParallelAnimation {
        id: enter
        NumberAnimation { target: root; property: "opacity"; to: 1; duration: 180 }
        NumberAnimation { target: slide; property: "y"; to: 0; duration: 220; easing.type: Easing.OutCubic }
    }
}
