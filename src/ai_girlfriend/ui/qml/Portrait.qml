import QtQuick
import QtQuick.Controls

// Expression portrait with animated transitions (spec §1). Uses the character's image
// asset when `source` is set, otherwise falls back to an emoji for the expression id.
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

    Accessible.role: Accessible.Graphic
    Accessible.name: qsTr("Portrait, expression: %1").arg(expression)

    Component.onCompleted: { shown = expression; shownSource = source }
    onExpressionChanged: swap.restart()

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

    // gentle "breathing" so the portrait never feels frozen
    Item {
        id: breath
        anchors.fill: parent
        SequentialAnimation on scale {
            running: root.visible && root.width > 120
            loops: Animation.Infinite
            NumberAnimation { to: 1.025; duration: 2400; easing.type: Easing.InOutSine }
            NumberAnimation { to: 1.0; duration: 2400; easing.type: Easing.InOutSine }
        }

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

        Item {
            id: face
            anchors.fill: parent
            transformOrigin: Item.Center

            // Crop the photo into a circle: fill the whole avatar and cut off
            // the overflow, clipped by a round mask so it reads as an avatar.
            Item {
                id: imageClip
                anchors.fill: parent
                anchors.margins: root.width * 0.08
                visible: root.shownSource !== "" && image.status === Image.Ready
                layer.enabled: true

                // Round mask used by layer to clip the image to a circle.
                Rectangle {
                    id: circleMask
                    anchors.fill: parent
                    radius: width / 2
                    color: "white"
                    visible: false
                    layer.enabled: true
                }

                Image {
                    id: image
                    anchors.fill: parent
                    source: root.shownSource
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                    smooth: true
                    layer.enabled: true
                    layer.samplerName: "source"
                    layer.effect: ShaderEffect {
                        property variant mask: ShaderEffectSource {
                            sourceItem: circleMask
                            hideSource: true
                        }
                        fragmentShader: "
                            varying highp vec2 qt_TexCoord0;
                            uniform lowp sampler2D source;
                            uniform lowp sampler2D mask;
                            uniform lowp float qt_Opacity;
                            void main() {
                                lowp vec4 tex = texture2D(source, qt_TexCoord0);
                                lowp vec4 m = texture2D(mask, qt_TexCoord0);
                                gl_FragColor = tex * m.a * qt_Opacity;
                            }"
                    }
                }
            }
            Text {
                anchors.centerIn: parent
                visible: root.shownSource === "" || root.shownSource === undefined
                text: root.emojiMap[root.shown] !== undefined ? root.emojiMap[root.shown] : "🙂"
                font.pixelSize: root.width * 0.46
            }
        }
    }
}
