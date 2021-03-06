// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM

Row {
    x: model.depth * UM.Theme.getSize("default_margin").width;

    UM.TooltipArea
    {
        width: height;
        height: check.height;

        text:
        {
            if(provider.properties.enabled == "True")
            {
                return ""
            }

            var requires = settingDefinitionsModel.getRequires(definition.key, "enabled")
            if(requires.length == 0)
            {
                return catalog.i18nc("@item:tooltip", "This setting has been disabled by the active machine and will not be visible.");
            }
            else
            {
                var requires_text = ""
                for(var i in requires)
                {
                    if(requires_text == "")
                    {
                        requires_text = requires[i].label
                    }
                    else
                    {
                        requires_text += ", " + requires[i].label
                    }
                }

                return catalog.i18ncp("@item:tooltip %1 is list of setting names", "This setting has been disabled by %1. It will only become visible after that setting is changed.", "This setting has been disabled by %1. It will only become visible after those settings are changed.", requires.length) .arg(requires_text);
            }
        }



        UM.RecolorImage
        {
            anchors.centerIn: parent

            width: check.height * 0.75
            height: width

            source: UM.Theme.getIcon("warning")

            color: palette.buttonText
        }

        visible: provider.properties.enabled == "False"
    }

    UM.TooltipArea
    {
        text: model.description;

        width: childrenRect.width;
        height: childrenRect.height;

        CheckBox
        {
            id: check

            text: definition.label
            checked: model.visible;
            enabled: !model.prohibited;

            MouseArea {
                anchors.fill: parent;
                onClicked: definitionsModel.setVisible(model.key, !check.checked);
            }
        }
    }

    UM.SettingPropertyProvider
    {
        id: provider

        containerStackId: "global"
        watchedProperties: [ "enabled" ]
        key: definition.key
    }

    UM.I18nCatalog { id: catalog; name: "uranium" }
    SystemPalette { id: palette }
}
