# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

import ast
import json
import enum
import collections

from UM.Logger import Logger

from . import SettingFunction


##  Type of definition property.
#
#   This enum describes the possible types for a supported definition property.
#   For more information about supported definition properties see SettingDefinition
#   and SettingDefinition::addSupportedProperty().
class DefinitionPropertyType(enum.IntEnum):
    Any = 1  ## Any value.
    String = 2  ## Value is always converted to string.
    TranslatedString = 3  ## Value is converted to string then passed through an i18nCatalog object to get a translated version of that string.
    Function = 4  ## Value is a python function. It is passed to SettingFunction's constructor which will parse and analyze it.


##  Defines a single Setting with its properties.
#
#   This class defines a single Setting with all its properties. This class is considered immutable,
#   the only way to change it is using deserialize(). Should any state need to be stored for a definition,
#   create a SettingInstance pointing to the definition, then store the value in that instance.
#
#   == Supported Properties
#
#   The SettingDefinition class contains a concept of "supported properties". These are properties that
#   are supported when serializing or deserializing the setting. These properties are defined through the
#   addSupportedProperty() method. Each property needs a name and a type. In addition, there are two
#   optional boolean value to indicate whether the property is "required" and whether it is "read only".
#   Currently, four types of supported properties are defined. Please DefinitionPropertyType for a description
#   of these types.
#
#   Required properties are properties that should be present when deserializing a setting. If the property
#   is not present, an error will be raised. Read-only properties are properties that should never change
#   after creating a SettingDefinition. This means they cannot be stored in a SettingInstance object.
class SettingDefinition:
    ##  Construcutor
    #
    #   \param key \type{string} The unique, machine readable/writable key to use for this setting.
    #   \param container \type{DefinitionContainer} The container of this setting. Defaults to None.
    #   \param parent \type{SettingDefinition} The parent of this setting. Defaults to None.
    #   \param i18n_catalog \type{i18nCatalog} The translation catalog to use for this setting. Defaults to None.
    def __init__(self, key, container = None, parent = None, i18n_catalog = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._key = key
        self._container = container
        self._parent = parent

        self._i18n_catalog = i18n_catalog

        self._children = []
        self._relations = []

        self.__property_values = {}

    ##  Override __getattr__ to provide access to definition properties.
    def __getattr__(self, name):
        if name in self.__property_definitions and name in self.__property_values:
            return self.__property_values[name]

        raise AttributeError("'SettingDefinition' object has no attribute '{0}'".format(name))

    ##  Override __setattr__ to enforce invariant status of definition properties.
    def __setattr__(self, name, value):
        if name in self.__property_definitions:
            raise NotImplementedError("Setting of property {0} not supported".format(name))

        super().__setattr__(name, value)

    ##  The key of this setting.
    #
    #   \return \type{string}
    @property
    def key(self):
        return self._key

    ##  The container of this setting.
    #
    #   \return \type{DefinitionContainer}
    @property
    def container(self):
        return self._container

    ##  The parent of this setting.
    #
    #   \return \type{SettingDefinition}
    @property
    def parent(self):
        return self._parent

    ##  A list of children of this setting.
    #
    #   \return \type{list<SettingDefinition>}
    @property
    def children(self):
        return self._children

    ##  A list of SettingRelation objects of this setting.
    #
    #   \return \type{list<SettingRelation>}
    @property
    def relations(self):
        return self._relations

    ##  Serialize this setting to a string.
    #
    #   \return \type{string} A serialized representation of this setting.
    def serialize(self):
        pass

    ##  Deserialize this setting from a string or dict.
    #
    #   \param serialized \type{string or dict} A serialized representation of this setting.
    def deserialize(self, serialized):
        if isinstance(serialized, dict):
            self._deserialize_dict(serialized)
        else:
            parsed = json.loads(serialized, object_pairs_hook=collections.OrderedDict)
            self._deserialize_dict(parsed)

    ##  Get a child by key
    #
    #   \param key \type{string} The key of the child to get.
    #
    #   \return \type{SettingDefinition} The child with the specified key or None if not found.
    def getChild(self, key):
        for child in self._children:
            if child.key == key:
                return child

        return None

    ##  Find all definitions matching certain criteria.
    #
    #   This will search this definition and its children for definitions matching the search criteria.
    #
    #   \param kwargs \type{dict} A dictionary of keyword arguments that need to match properties of the children.
    #
    #   \return \type{list} A list of children matching the search criteria. The list will be empty if no children were found.
    def findDefinitions(self, **kwargs):
        definitions = []

        has_properties = True
        for key, value in kwargs.items():
            try:
                if getattr(self, key) != value:
                    has_properties = False
            except AttributeError:
                has_properties = False

        if has_properties:
            definitions.append(self)

        for child in self._children:
            definitions.extend(child.findDefinitions(**kwargs))

        return definitions

    def __repr__(self):
        return "<SettingDefinition (0x{0:x}) key={1} container={2}>".format(id(self), self._key, self._container)

    ##  Define a new supported property for SettingDefinitions.
    #
    #   Since applications may want custom properties in their definitions, most properties are handled
    #   dynamically. This allows the application to define what extra properties it wants to support.
    #   Additionally, it can indicate whether a properties should be considered "required". When a
    #   required property is not missing during deserialization, an AttributeError will be raised.
    #
    #   \param name \type{string} The name of the property to define.
    #   \param property_type \type{DefinitionPropertyType} The type of property.
    #   \param kwargs Keyword arguments. Possible values:
    #                 required \type{bool} True if missing the property indicates an error should be raised. Defaults to False.
    #                 read_only \type{bool} True if the property should never be set on a SettingInstance. Defaults to False. Note that for Function properties this indicates whether the result of the function should be stored.
    @classmethod
    def addSupportedProperty(cls, name, property_type, **kwargs):
        cls.__property_definitions[name] = {"type": property_type, "required": kwargs.get("required", False), "read_only": kwargs.get("read_only", False)}

    ##  Get the names of all supported properties.
    #
    #   \param type \type{DefinitionPropertyType} The type of property to get the name of. Defaults to None which means all properties.
    #
    #   \return A list of all the names of supported properties.
    @classmethod
    def getPropertyNames(cls, type = None):
        result = []
        for key, value in cls.__property_definitions.items():
            if not type or value["type"] == type:
                result.append(key)
        return result

    ##  Check if a property with the specified name is defined as a supported property.
    #
    #   \param name \type{string} The name of the property to check if it is supported.
    #
    #   \return True if the property is supported, False if not.
    @classmethod
    def hasProperty(cls, name):
        return name in cls.__property_definitions

    ##  Check if the specified property is considered a required property.
    #
    #   Required properties are checked when deserializing a SettingDefinition and if not present an error
    #   will be reported.
    #
    #   \param name \type{string} The name of the property to check if it is required or not.
    #
    #   \return True if the property is supported and is required, False if it is not required or is not part of the list of supported properties.
    @classmethod
    def isRequiredProperty(cls, name):
        if name in cls.__property_definitions:
            return cls.__property_definitions[name]["required"]
        return False

    ##  Check if the specified property is considered a read-only property.
    #
    #   Read-only properties are properties that cannot have their value set in SettingInstance objects.
    #
    #   \param name \type{string} The name of the property to check if it is read-only or not.
    #
    #   \return True if the property is supported and is read-only, False if it is not required or is not part of the list of supported properties.
    @classmethod
    def isReadOnlyProperty(cls, name):
        if name in cls.__property_definitions:
            return cls.__property_definitions[name]["read_only"]
        return False

    ##  Add a new setting type to the list of accepted setting types.
    #
    #   \param type_name The name of the new setting type.
    #   \param from_string A function to call that converts to a proper value of this type from a string.
    #   \param to_string A function that converts a value of this type to a string.
    #
    @classmethod
    def addSettingType(cls, type_name, from_string, to_string):
        cls.__type_definitions[type_name] = { "from": from_string, "to": to_string }

    ##  Convert a string to a value according to a setting type.
    #
    #   \param type_name \type{string} The name of the type to convert to.
    #   \param string_value \type{string} The string to convert.
    #
    #   \return The string converted to a proper value.
    #
    #   \exception ValueError Raised when the specified type does not exist.
    @classmethod
    def settingValueFromString(cls, type_name, string_value):
        if type_name not in cls.__type_definitions:
            raise ValueError("Unknown setting type {0}".format(type_name))

        convert_function = cls.__type_definitions[type_name]["to"]
        if convert_function:
            return convert_function(string_value)

        return string_value

    ##  Convert a setting value to a string according to a setting type.
    #
    #   \param type_name \type{string} The name of the type to convert from.
    #   \param value The value to convert.
    #
    #   \return \type{string} The specified value converted to a string.
    #
    #   \exception ValueError Raised when the specified type does not exist.
    @classmethod
    def settingValueToString(cls, type_name, value):
        if type_name not in cls.__type_definitions:
            raise ValueError("Unknown setting type {0}".format(type_name))

        convert_function = cls.__type_definitions[type_name]["from"]
        if convert_function:
            return convert_function(value)

        return value

    ## protected:

    # Deserialize from a dictionary
    def _deserialize_dict(self, serialized):
        self._children = []
        self._relations = []
        self._type = "unknown"

        for key, value in serialized.items():
            if key == "children":
                for child_key, child_dict in value.items():
                    child = SettingDefinition(child_key, self._container, self, self._i18n_catalog)
                    child.deserialize(child_dict)
                    self._children.append(child)
                continue

            if key not in self.__property_definitions:
                Logger.log("w", "Unrecognised property %s in setting %s", key, self._key)
                continue

            if key == "type":
                if value not in self.__type_definitions:
                    raise ValueError("Type {0} is not a correct setting type".format(value))

            if self.__property_definitions[key]["type"] == DefinitionPropertyType.Any:
                self.__property_values[key] = value
            elif self.__property_definitions[key]["type"] == DefinitionPropertyType.String:
                self.__property_values[key] = str(value)
            elif self.__property_definitions[key]["type"] == DefinitionPropertyType.TranslatedString:
                self.__property_values[key] = self._i18n_catalog.i18n(str(value)) if self._i18n_catalog is not None else value
            elif self.__property_definitions[key]["type"] == DefinitionPropertyType.Function:
                self.__property_values[key] = SettingFunction.SettingFunction(str(value))

        for key in filter(lambda i: self.__property_definitions[i]["required"], self.__property_definitions):
            if key not in self.__property_values:
                raise AttributeError("Setting {0} is missing required property {1}".format(self._key, key))

    __property_definitions = {
        # The name of the setting. Only used for display purposes.
        "label": {"type": DefinitionPropertyType.TranslatedString, "required": True, "read_only": True},
        # The type of setting. Can be any one of the types defined.
        "type": {"type": DefinitionPropertyType.String, "required": True, "read_only": True},
        # An optional icon that can be displayed for the setting.
        "icon": {"type": DefinitionPropertyType.String, "required": False, "read_only": True},
        # A string describing the unit used for the setting. This is only used for display purposes at the moment.
        "unit": {"type": DefinitionPropertyType.String, "required": False, "read_only": True},
        # A description of what the setting does. Used for display purposes.
        "description": {"type": DefinitionPropertyType.TranslatedString, "required": True, "read_only": True},
        # A description of what is wrong when the setting has a warning validation state. Used for display purposes.
        "warning_description": {"type": DefinitionPropertyType.TranslatedString, "required": False, "read_only": True},
        # A description of what is wrong when the setting has an error validation state. Used for display purposes.
        "error_description": {"type": DefinitionPropertyType.TranslatedString, "required": False, "read_only": True},
        # The default value of the setting. Used when no value function is defined.
        "default_value": {"type": DefinitionPropertyType.Any, "required": False, "read_only": True},
        # A function used to calculate the value of the setting.
        "value": {"type": DefinitionPropertyType.Function, "required": False, "read_only": False},
        # A function that should evaluate to a boolean to indicate whether or not the setting is enabled.
        "enabled": {"type": DefinitionPropertyType.Function, "required": False, "read_only": False},
        # A function that calculates the minimum value for this setting. If the value is less than this, validation will indicate an error.
        "minimum_value": {"type": DefinitionPropertyType.Function, "required": False, "read_only": False},
        # A function that calculates the maximum value for this setting. If the value is more than this, validation will indicate an error.
        "maximum_value": {"type": DefinitionPropertyType.Function, "required": False, "read_only": False},
        # A function that calculates the minimum warning value for this setting. If the value is less than this, validation will indicate a warning.
        "minimum_value_warning": {"type": DefinitionPropertyType.Function, "required": False, "read_only": False},
        # A function that calculates the maximum warning value for this setting. If the value is more than this, validation will indicate a warning.
        "maximum_value_warning": {"type": DefinitionPropertyType.Function, "required": False, "read_only": False},
        # A dictionary of key-value pairs that provide the options for an enum type setting. The key is the actual value, the value is a translated display string.
        "options": {"type": DefinitionPropertyType.Any, "required": False, "read_only": True},
        "comments": {"type": DefinitionPropertyType.String, "required": False, "read_only": True}
    }

    __type_definitions = {
        # An integer value
        "int": {"from": str, "to": ast.literal_eval},
        # A boolean value
        "bool": {"from": str, "to": ast.literal_eval},
        # Special case setting; Doesn't have a value. Display purposes only.
        "category": {"from": None, "to": None},
        # A string value
        "str": {"from": None, "to": None},
        # An enumeration
        "enum": {"from": None, "to": None},
        # A floating point value
        "float": {"from": str, "to": lambda v: ast.literal_eval(v.replace(",", "."))},
        # A list of 2D points
        "polygon": {"from": None, "to": None},
        # A list of polygons
        "polygons": {"from": None, "to": None},
        # A 3D point
        "vec3": {"from": None, "to": None},
    }