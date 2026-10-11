import QtQuick
import ".."

Rectangle {
    id: root
    implicitWidth: 64
    implicitHeight: 40
    radius: 20
    color: Theme.assistantBubble

    Accessible.role: Accessible.Animation
    Accessible.name: qsTr("Typing")

    Row {
        anchors.centerIn: parent
        spacing: 6
        Repeater {
            model: 3
            Rectangle {
                id: dot
                width: 8
                height: 8
                radius: 4
                color: Theme.onAssistantBubble
                opacity: 0.3
                SequentialAnimation {
                    running: root.visible
                    loops: Animation.Infinite
                    PauseAnimation { duration: index * 160 }
                    NumberAnimation { target: dot; property: "opacity"; to: 1; duration: 280 }
                    NumberAnimation { target: dot; property: "opacity"; to: 0.3; duration: 280 }
                    PauseAnimation { duration: (2 - index) * 160 }
                }
            }
        }
    }
}
