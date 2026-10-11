import QtQuick
import QtQuick.Controls

// One message (spec §7.1). User = right / userBubble, assistant = left / assistantBubble.
Item {
    id: root
    property string role: "assistant"
    property string text: ""
    readonly property bool isUser: role === "user"

    readonly property real padH: 16
    readonly property real padV: 11
    readonly property real maxBubble: Math.min(width * 0.8, 560)

    width: ListView.view ? ListView.view.width : 400
    height: bubble.height + 8

    Accessible.role: Accessible.StaticText
    Accessible.name: (isUser ? qsTr("You") : qsTr("Companion")) + ": " + text

    TextMetrics { id: metrics; font: body.font; text: root.text }

    Rectangle {
        id: bubble
        anchors.left: root.isUser ? undefined : parent.left
        anchors.right: root.isUser ? parent.right : undefined
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        width: Math.min(Math.ceil(metrics.boundingRect.width) + 2, root.maxBubble - 2 * root.padH) + 2 * root.padH
        height: body.contentHeight + 2 * root.padV
        radius: 18
        color: root.isUser ? Theme.userBubble : Theme.assistantBubble
        Behavior on color { ColorAnimation { duration: Theme.durationMedium } }

        TextEdit {
            id: body
            x: root.padH
            y: root.padV
            width: bubble.width - 2 * root.padH
            text: root.text
            readOnly: true
            selectByMouse: true
            wrapMode: TextEdit.Wrap
            textFormat: TextEdit.PlainText
            color: root.isUser ? Theme.onUserBubble : Theme.onAssistantBubble
            selectionColor: Theme.primary
            selectedTextColor: Theme.onPrimary
            font.pixelSize: Theme.fontSizeM
        }
    }

    opacity: 0
    transform: Translate { id: slide; y: 14 }
    Component.onCompleted: enter.start()
    ParallelAnimation {
        id: enter
        NumberAnimation { target: root; property: "opacity"; to: 1; duration: 220 }
        NumberAnimation { target: slide; property: "y"; to: 0; duration: 260; easing.type: Easing.OutCubic }
    }
}
