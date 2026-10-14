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
    property string draftTemperature: ""
    property string draftMaxTokens: ""
    // expression id -> asset path
    property var draftPhotos: ({})

    // Which path the image browser fills: "" (new row) or an expression id.
    property string browseTarget: ""

    function applyBrowsedFile(path) {
        if (view.browseTarget === "") {
            newExprPath.text = path
        } else {
            var p = Object.assign({}, view.draftPhotos)
            p[view.browseTarget] = path
            view.draftPhotos = p
        }
    }

    Component.onCompleted: {
        if (isEditing) {
            var info = Backends.settings.characterInfo(characterId)
            draftName = info.name
            draftPersonality = info.personality
            draftGreeting = info.greeting_message
            draftExpression = info.expression
            draftTemperature = info.temperature !== "" ? String(info.temperature) : ""
            draftMaxTokens = info.max_tokens !== "" ? String(info.max_tokens) : ""
            draftPhotos = Backends.settings.characterPhotos(characterId)
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

            // Response tuning: sampling temperature + approximate length.
            Label {
                text: qsTr("Response tuning")
                color: Theme.onSurface
                font.pixelSize: Theme.fontSizeM + 1
                font.weight: Font.Medium
                Layout.topMargin: 8
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Label {
                        text: qsTr("Temperature")
                        color: Theme.onSurfaceVariant
                        font.pixelSize: Theme.fontSizeS + 1
                    }
                    TextField {
                        Layout.fillWidth: true
                        placeholderText: qsTr("e.g. 0.8")
                        text: view.draftTemperature
                        color: Theme.onSurface
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        validator: DoubleValidator { bottom: 0.0; top: 2.0; decimals: 2 }
                        onTextEdited: view.draftTemperature = text
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Label {
                        text: qsTr("Max length (tokens)")
                        color: Theme.onSurfaceVariant
                        font.pixelSize: Theme.fontSizeS + 1
                    }
                    TextField {
                        Layout.fillWidth: true
                        placeholderText: qsTr("e.g. 512")
                        text: view.draftMaxTokens
                        color: Theme.onSurface
                        inputMethodHints: Qt.ImhDigitsOnly
                        validator: IntValidator { bottom: 1; top: 100000 }
                        onTextEdited: view.draftMaxTokens = text
                    }
                }
            }
            Label {
                Layout.fillWidth: true
                text: qsTr("Higher temperature = more creative; lower = more focused. " +
                           "Leave empty to use the global default.")
                color: Theme.onSurfaceVariant
                wrapMode: Text.Wrap
                font.pixelSize: Theme.fontSizeS
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
                        glyph: "📂"
                        fg: Theme.onSurfaceVariant
                        accessibleName: qsTr("Browse for image")
                        implicitWidth: 36; implicitHeight: 36
                        onClicked: {
                            view.browseTarget = modelData
                            fileBrowser.open()
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
                IconButton {
                    glyph: "📂"
                    fg: Theme.onSurfaceVariant
                    accessibleName: qsTr("Browse for image")
                    implicitWidth: 40; implicitHeight: 40
                    onClicked: {
                        view.browseTarget = ""
                        fileBrowser.open()
                    }
                }
                Button {
                    text: qsTr("Add")
                    contentItem: Text {
                        text: parent.text
                        color: Theme.onSurface
                        font: parent.font
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        opacity: parent.enabled ? 1.0 : 0.5
                    }
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

    // In-app image browser (read-only filesystem backend exposed to QML).
    FileBrowser {
        id: fileBrowser
        onFileSelected: function(path) { view.applyBrowsedFile(path) }
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
                enabled: !Backends.settings.busy
                contentItem: Text {
                    text: parent.text
                    color: Theme.onSurface
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    opacity: parent.enabled ? 1.0 : 0.5
                }
                onClicked: {
                    if (Backends.settings.deleteCharacter(view.characterId)) {
                        view.StackView.view.pop()
                    } else {
                        Backends.chat.errorRaised(qsTr("Built-in characters cannot be deleted."))
                    }
                }
            }
            Item { Layout.fillWidth: true }
            Button {
                text: qsTr("Save")
                highlighted: true
                enabled: !Backends.settings.busy
                contentItem: Text {
                    text: parent.text
                    color: Theme.onPrimary
                    font: parent.font
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    opacity: parent.enabled ? 1.0 : 0.5
                }
                onClicked: {
                    var payload = {
                        "name": view.draftName,
                        "personality": view.draftPersonality,
                        "greeting_message": view.draftGreeting,
                        "initial_expression": view.draftExpression.length > 0
                                                ? view.draftExpression : "neutral",
                        "temperature": view.draftTemperature,
                        "max_tokens": view.draftMaxTokens,
                        "photo_emoji_map": view.draftPhotos,
                        "original_id": view.characterId
                    }
                    var id = Backends.settings.saveCharacter(payload)
                    if (id.length > 0) {
                        view.StackView.view.pop()
                    } else {
                        Backends.chat.errorRaised(qsTr("Invalid character: a name is required."))
                    }
                }
            }
        }
    }
}
