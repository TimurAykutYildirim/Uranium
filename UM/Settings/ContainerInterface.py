# Copyright (c) 2016 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

import UM.Decorators

##  Shared interface between setting container types
#
@UM.Decorators.interface
class ContainerInterface:
    ##  Get the ID of the container.
    #
    #   The ID should be unique, machine readable and machine writable. It is
    #   intended to be used for example when referencing the container in
    #   configuration files or when writing a file to disk.
    #
    #   \return \type{string} The unique ID of this container.
    def getId(self):
        pass

    ##  Get the human-readable name of this container.
    #
    #   This should return a human-readable name for the container, that can be
    #   used in the interface.
    #
    #   \return \type{string} The name of this container.
    def getName(self):
        pass

    ##  Get all metadata of this container.
    #
    #   This returns a dictionary containing all the metadata for this container.
    #   How this metadata is used depends on the application.
    #
    #   \return \type{dict} The metadata for this container.
    def getMetaData(self):
        pass

    ##  Get the value of a single metadata entry.
    #
    #   \param entry \type{string} The key of the metadata to retrieve.
    #   \param default The default value to return if the entry cannot be found.
    #
    #   \return The value of the metadata corresponding to `name`, or `default`
    #           when the entry could not be found.
    def getMetaDataEntry(self, entry, default = None):
        pass

    ##  Get the value of a property of the container item.
    #
    #   \param key \type{string} The key of the item to retrieve a property from.
    #   \param name \type{string} The name of the property to retrieve.
    #
    #   \return The specified property value of the container item corresponding to key, or None if not found.
    def getProperty(self, key, property_name):
        pass

    ##  Serialize this container to a string.
    #
    #   The serialized representation of the container can be used to write the
    #   container to disk or send it over the network.
    #
    #   \return \type{string} A string representation of this container.
    def serialize(self):
        pass

    ##  Deserialize the container from a string representation.
    #
    #   This should replace the contents of this container with those in the serialized
    #   represenation.
    #
    #   \param serialized A serialized string containing a container that should be deserialized.
    def deserialize(self, serialized):
        pass