import QtQuick
import QtQuick.Controls
import ".."

AbstractButton {
    id: btn
    property string glyph: ""
    property string accessibleName: ""
    property bool filled: false
    property color fg: filled ? Theme.onPrimary : Theme.onSurfaceVariant
    implicitWidth: 42
    implicitHeight: 42
    focusPolicy: Qt.TabFocus
    hoverEnabled: true
    Accessible.role: Accessible.Button
    Accessible.name: accessibleName
    Accessible.description: accessibleName
    ToolTip.visible: hovered && accessibleName.length > 0
    ToolTip.delay: 500
    ToolTip.text: accessibleName
    contentItem: Text {
        text: btn.glyph; color: btn.fg
        opacity: btn.enabled ? 1.0 : 0.35
        font.pixelSize: btn.filled ? 23 : 20
        font.weight: Font.Medium
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
        radius: btn.filled ? 15 : 14
        color: btn.filled ? (btn.enabled ? Theme.primary : Theme.surfaceVariant)
             : ((btn.hovered || btn.down) && btn.enabled ? Theme.surfaceVariant : "transparent")
        border.width: btn.visualFocus ? 2 : (btn.filled ? 0 : 1)
        border.color: btn.visualFocus ? Theme.primary : Qt.alpha(Theme.outline, 0.14)
        scale: btn.down ? 0.93 : 1.0
        Behavior on scale { NumberAnimation { duration: 90 } }
        Behavior on color { ColorAnimation { duration: 120 } }
    }
}
