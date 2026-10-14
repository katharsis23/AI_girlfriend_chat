import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects

// Expression portrait with animated transitions (spec §1).
//
// Shows the character's image when `source` is set, otherwise an emoji for the
// expression id. The photo is cropped into a circle with OpacityMask — the
// classic Qt recipe (a round, layered mask + the image), which is simpler and
// far more reliable than a hand-written ShaderEffect mask.
Item {
    id: root
    property string expression: "neutral"
    property string source: ""

    property string shown: expression
    property string shownSource: source

    implicitWidth: 200
    implicitHeight: 200

    readonly property var emojiMap: ({
        "neutral": "🙂", "happy": "😊", "shy": "😳", "thinking": "🤔", "sad": "😢",
        "surprised": "😮", "angry": "😠", "love": "😍", "sleepy": "😴", "smile": "😊"
    })

    readonly property bool hasImage: shownSource !== "" && photo.status === Image.Ready

    Accessible.role: Accessible.Graphic
    Accessible.name: qsTr("Portrait, expression: %1").arg(expression)

    onExpressionChanged: swap.restart()
    onSourceChanged: swap.restart()

    SequentialAnimation {
        id: swap
        ParallelAnimation {
            NumberAnimation { target: face; property: "opacity"; to: 0; duration: 140 }
            NumberAnimation { target: face; property: "scale"; to: 0.92; duration: 140 }
        }
        ScriptAction { script: { root.shown = root.expression; root.shownSource = root.source } }
        ParallelAnimation {
            NumberAnimation { target: face; property: "opacity"; to: 1; duration: 240 }
            NumberAnimation { target: face; property: "scale"; to: 1; duration: 240; easing.type: Easing.OutBack }
        }
    }

    // Gentle "breathing" so the portrait never feels frozen.
    Item {
        id: face
                anchors.fill: parent
        transformOrigin: Item.Center

        SequentialAnimation on scale {
            running: root.visible && root.width > 120
            loops: Animation.Infinite
            NumberAnimation { to: 1.025; duration: 2400; easing.type: Easing.InOutSine }
            NumberAnimation { to: 1.0; duration: 2400; easing.type: Easing.InOutSine }
        }

        // Circle background + border behind the photo.
        Rectangle {
            id: halo
            anchors.fill: parent
            radius: width / 2
            color: Theme.surfaceVariant
            border.width: Math.max(2, root.width / 70)
            border.color: Theme.primary
            Behavior on color { ColorAnimation { duration: Theme.durationMedium } }
            Behavior on border.color { ColorAnimation { duration: Theme.durationMedium } }
        }

        // The photo, already sized to the inner circle.
        Image {
            id: photo
            anchors.fill: parent
            anchors.margins: Math.max(2, root.width / 70) + root.width * 0.06
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                smooth: true
                cache: true
                visible: false
                    source: root.shownSource
            sourceSize.width: Math.max(1, Math.round(width))
            sourceSize.height: Math.max(1, Math.round(height))
            }

        // Round mask used to crop the photo. It must be rendered for the mask
        // to have content, but we hide it with layer.enabled so only the crop
        // is shown (the standard OpacityMask recipe).
        Rectangle {
            id: mask
                anchors.fill: photo
            radius: width / 2
            color: "white"
            visible: false
            layer.enabled: true
            }

        OpacityMask {
            anchors.fill: photo
            visible: root.hasImage
            source: photo
            maskSource: mask
            }

        // Emoji fallback when there is no usable image.
        Text {
            anchors.centerIn: parent
            visible: !root.hasImage
            text: root.emojiMap[root.shown] !== undefined ? root.emojiMap[root.shown] : "🙂"
            font.pixelSize: root.width * 0.46
    }
}
}
