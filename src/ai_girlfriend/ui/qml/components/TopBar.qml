import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Rectangle {
    id: bar
    property string title: ""
    property string subtitle: ""
    property bool showBack: false
    signal backClicked()
    default property alias actions: actionRow.data

    implicitHeight: 64
    color: Theme.surface
    Behavior on color { ColorAnimation { duration: Theme.durationMedium } }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        spacing: 4

        IconButton {
            visible: bar.showBack
            glyph: "←"
            accessibleName: qsTr("Back")
            onClicked: bar.backClicked()
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.leftMargin: bar.showBack ? 0 : 12
            spacing: 0
            Label {
                Layout.fillWidth: true
                text: bar.title
                elide: Text.ElideRight
                color: Theme.onSurface
                font.pixelSize: Theme.fontSizeL
                font.weight: Font.Medium
            }
            Label {
                Layout.fillWidth: true
                visible: bar.subtitle.length > 0
                text: bar.subtitle
                elide: Text.ElideRight
                color: Theme.primary
                font.pixelSize: Theme.fontSizeS
            }
        }
        Row { id: actionRow; spacing: 4 }
    }
    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: Theme.surfaceVariant
    }
}
