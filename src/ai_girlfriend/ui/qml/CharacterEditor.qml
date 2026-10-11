import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

// Create or edit a character (persistence handled by SettingsBackend).
// Pass `characterId` to edit an existing character, or leave it empty to add.
Page {
    id: view
    property string characterId: ""
    readonly property bool isEditing: characterId.length > 0

    property string draftName: ""
    property string draftPersonality: ""
    property string draftGreeting: ""
    property string draftExpression: "neutral"
    // expression id -> asset path
    property var draftPhotos: ({})

    Component.onCompleted: {
        if (isEditing) {
            var info = settingsBackend.characterInfo(characterId)
            draftName = info.name
            draftPersonality = info.personality
            draftGreeting = info.greeting_message
            draftExpression = info.expression
            draftPhotos = settingsBackend.characterPhotos(characterId)
        } else {
            draftPhotos = ({})
        }
    }

    background: Rectangle { color: Theme.background }

    header: TopBar {
        title: view.isEditing ? qsTr("Edit character") : qsTr("New character")
        showBack: true
        onBackClicked: view.StackView.view.pop()
    }

    ScrollView {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: bottomBar.top
        clip: true

        ColumnLayout {
            width: Math.min(view.width - 32, 640)
            x: (view.width - width) / 2
            spacing: 12

            Label { text: qsTr("Name"); color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS + 1 }
            TextField {
                Layout.fillWidth: true
                placeholderText: qsTr("e.g. Aria")
                text: view.draftName
                color: Theme.onSurface
                onTextEdited: view.draftName = text
            }

            Label { text: qsTr("Personality"); color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS + 1 }
            TextArea {
                Layout.fillWidth: true
                Layout.preferredHeight: 96
                wrapMode: TextArea.Wrap
                placeholderText: qsTr("A warm, caring companion…")
                text: view.draftPersonality
                color: Theme.onSurface
                onTextChanged: view.draftPersonality = text
            }

            Label { text: qsTr("Greeting"); color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS + 1 }
            TextField {
                Layout.fillWidth: true
                placeholderText: qsTr("Hi! I missed you.")
                text: view.draftGreeting
                color: Theme.onSurface
                onTextEdited: view.draftGreeting = text
            }

            Label { text: qsTr("Initial expression"); color: Theme.onSurfaceVariant; font.pixelSize: Theme.fontSizeS + 1 }
            TextField {
                Layout.fillWidth: true
                placeholderText: qsTr("neutral")
                text: view.draftExpression
                color: Theme.onSurface
                onTextEdited: view.draftExpression = text
            }

            // Expression image paths: id + absolute file path.
            Label {
                text: qsTr("Expression images")
                color: Theme.onSurface
                font.pixelSize: Theme.fontSizeM + 1
                font.weight: Font.Medium
                Layout.topMargin: 8
            }
            Label {
                text: qsTr("Map an expression id to an image path on disk.")
                color: Theme.onSurfaceVariant
                font.pixelSize: Theme.fontSizeS + 1
            }

            Repeater {
                model: Object.keys(view.draftPhotos)
                delegate: RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    Label { text: modelData; color: Theme.onSurfaceVariant; Layout.preferredWidth: 100; elide: Text.ElideRight }
                    TextField {
                        Layout.fillWidth: true
                        text: view.draftPhotos[modelData]
                        color: Theme.onSurface
                        onTextEdited: {
                            var p = Object.assign({}, view.draftPhotos)
                            p[modelData] = text
                            view.draftPhotos = p
                        }
                    }
                    IconButton {
                        glyph: "✕"
                        fg: Theme.onSurfaceVariant
                        accessibleName: qsTr("Remove expression")
                        implicitWidth: 36; implicitHeight: 36
                        onClicked: {
                            var p = Object.assign({}, view.draftPhotos)
                            delete p[modelData]
                            view.draftPhotos = p
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12
                TextField {
                    id: newExprId
                    Layout.preferredWidth: 140
                    placeholderText: qsTr("expression id")
                    color: Theme.onSurface
                }
                TextField {
                    id: newExprPath
                    Layout.fillWidth: true
                    placeholderText: qsTr("/path/to/image.png")
                    color: Theme.onSurface
                }
                Button {
                    text: qsTr("Add")
                    onClicked: {
                        if (newExprId.text.length > 0 && newExprPath.text.length > 0) {
                            var p = Object.assign({}, view.draftPhotos)
                            p[newExprId.text] = newExprPath.text
                            view.draftPhotos = p
                            newExprId.text = ""
                            newExprPath.text = ""
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        id: bottomBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 72
        color: Theme.surface

        RowLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            Button {
                visible: view.isEditing
                text: qsTr("Delete")
                enabled: !settingsBackend.busy
                onClicked: {
                    if (settingsBackend.deleteCharacter(view.characterId)) {
                        view.StackView.view.pop()
                    } else {
                        chatBackend.errorRaised(qsTr("Built-in characters cannot be deleted."))
                    }
                }
            }
            Item { Layout.fillWidth: true }
            Button {
                text: qsTr("Save")
                highlighted: true
                enabled: !settingsBackend.busy
                onClicked: {
                    var payload = {
                        "name": view.draftName,
                        "personality": view.draftPersonality,
                        "greeting_message": view.draftGreeting,
                        "initial_expression": view.draftExpression.length > 0
                                                ? view.draftExpression : "neutral",
                        "photo_emoji_map": view.draftPhotos,
                        "original_id": view.characterId
                    }
                    var id = settingsBackend.saveCharacter(payload)
                    if (id.length > 0) {
                        view.StackView.view.pop()
                    } else {
                        chatBackend.errorRaised(qsTr("Invalid character: a name is required."))
                    }
                }
            }
        }
    }
}
