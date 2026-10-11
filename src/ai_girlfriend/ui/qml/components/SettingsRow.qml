import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

AbstractButton {
    id: row
    property string title: ""
    property string subtitle: ""
    property string glyph: ""

    implicitHeight: 80
    padding: 16
    hoverEnabled: true
    Accessible.role: Accessible.Button
    Accessible.name: title
    Accessible.description: subtitle

    background: Rectangle {
        radius: Theme.radius
        color: row.down || row.hovered ? Theme.surfaceVariant : Theme.surface
        border.width: row.visualFocus ? 2 : 0
        border.color: Theme.primary
        Behavior on color { ColorAnimation { duration: 120 } }
    }
    contentItem: RowLayout {
        spacing: 16
        Rectangle {
            Layout.preferredWidth: 44
            Layout.preferredHeight: 44
            radius: 22
            color: Theme.surfaceVariant
            Text { anchors.centerIn: parent; text: row.glyph; font.pixelSize: 20 }
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Label { text: row.title; color: Theme.onSurface; font.pixelSize: Theme.fontSizeM + 1; font.weight: Font.Medium }
            Label { text: row.subtitle; color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS + 1 }
        }
        Text { text: "›"; color: Theme.onSurfaceVariant; font.pixelSize: 26 }
    }
}
