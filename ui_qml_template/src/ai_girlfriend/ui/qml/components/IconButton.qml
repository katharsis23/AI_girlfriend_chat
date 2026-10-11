import QtQuick
import QtQuick.Controls
import ".."

// Round icon button; `filled: true` gives the M3 FilledIconButton look.
AbstractButton {
    id: btn
    property string glyph: ""
    property string accessibleName: ""
    property bool filled: false
    property color fg: filled ? Theme.onPrimary : Theme.onSurfaceVariant

    implicitWidth: 48
    implicitHeight: 48
    focusPolicy: Qt.TabFocus
    hoverEnabled: true

    Accessible.role: Accessible.Button
    Accessible.name: accessibleName
    Accessible.description: accessibleName
    ToolTip.visible: hovered && accessibleName.length > 0
    ToolTip.delay: 600
    ToolTip.text: accessibleName

    contentItem: Text {
        text: btn.glyph
        color: btn.fg
        opacity: btn.enabled ? 1.0 : 0.38
        font.pixelSize: btn.filled ? 24 : 20
        font.bold: btn.filled
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
        radius: width / 2
        color: btn.filled
               ? (btn.enabled ? Theme.primary : Theme.surfaceVariant)
               : ((btn.hovered || btn.down) && btn.enabled ? Theme.surfaceVariant : "transparent")
        border.width: btn.visualFocus ? 2 : 0
        border.color: Theme.primary
        scale: btn.down ? 0.92 : 1.0
        Behavior on scale { NumberAnimation { duration: 90 } }
        Behavior on color { ColorAnimation { duration: 120 } }
    }
}
