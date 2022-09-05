# coding: utf-8

"""
    Space Tycoon

    Space Tycoon server.  # noqa: E501

    OpenAPI spec version: 1.0.0
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401

import six

class Ship(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'ship_class': 'str',
        'life': 'int',
        'name': 'str',
        'player': 'str',
        'position': 'Coordinates',
        'prev_position': 'Coordinates',
        'resources': 'Resources',
        'command': 'Command'
    }

    attribute_map = {
        'ship_class': 'shipClass',
        'life': 'life',
        'name': 'name',
        'player': 'player',
        'position': 'position',
        'prev_position': 'prevPosition',
        'resources': 'resources',
        'command': 'command'
    }

    def __init__(self, ship_class=None, life=None, name=None, player=None, position=None, prev_position=None, resources=None, command=None):  # noqa: E501
        """Ship - a model defined in Swagger"""  # noqa: E501
        self._ship_class = None
        self._life = None
        self._name = None
        self._player = None
        self._position = None
        self._prev_position = None
        self._resources = None
        self._command = None
        self.discriminator = None
        self.ship_class = ship_class
        self.life = life
        self.name = name
        self.player = player
        self.position = position
        self.prev_position = prev_position
        self.resources = resources
        if command is not None:
            self.command = command

    @property
    def ship_class(self):
        """Gets the ship_class of this Ship.  # noqa: E501


        :return: The ship_class of this Ship.  # noqa: E501
        :rtype: str
        """
        return self._ship_class

    @ship_class.setter
    def ship_class(self, ship_class):
        """Sets the ship_class of this Ship.


        :param ship_class: The ship_class of this Ship.  # noqa: E501
        :type: str
        """
        if ship_class is None:
            raise ValueError("Invalid value for `ship_class`, must not be `None`")  # noqa: E501

        self._ship_class = ship_class

    @property
    def life(self):
        """Gets the life of this Ship.  # noqa: E501


        :return: The life of this Ship.  # noqa: E501
        :rtype: int
        """
        return self._life

    @life.setter
    def life(self, life):
        """Sets the life of this Ship.


        :param life: The life of this Ship.  # noqa: E501
        :type: int
        """
        if life is None:
            raise ValueError("Invalid value for `life`, must not be `None`")  # noqa: E501

        self._life = life

    @property
    def name(self):
        """Gets the name of this Ship.  # noqa: E501


        :return: The name of this Ship.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this Ship.


        :param name: The name of this Ship.  # noqa: E501
        :type: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def player(self):
        """Gets the player of this Ship.  # noqa: E501


        :return: The player of this Ship.  # noqa: E501
        :rtype: str
        """
        return self._player

    @player.setter
    def player(self, player):
        """Sets the player of this Ship.


        :param player: The player of this Ship.  # noqa: E501
        :type: str
        """
        if player is None:
            raise ValueError("Invalid value for `player`, must not be `None`")  # noqa: E501

        self._player = player

    @property
    def position(self):
        """Gets the position of this Ship.  # noqa: E501


        :return: The position of this Ship.  # noqa: E501
        :rtype: Coordinates
        """
        return self._position

    @position.setter
    def position(self, position):
        """Sets the position of this Ship.


        :param position: The position of this Ship.  # noqa: E501
        :type: Coordinates
        """
        if position is None:
            raise ValueError("Invalid value for `position`, must not be `None`")  # noqa: E501

        self._position = position

    @property
    def prev_position(self):
        """Gets the prev_position of this Ship.  # noqa: E501


        :return: The prev_position of this Ship.  # noqa: E501
        :rtype: Coordinates
        """
        return self._prev_position

    @prev_position.setter
    def prev_position(self, prev_position):
        """Sets the prev_position of this Ship.


        :param prev_position: The prev_position of this Ship.  # noqa: E501
        :type: Coordinates
        """
        if prev_position is None:
            raise ValueError("Invalid value for `prev_position`, must not be `None`")  # noqa: E501

        self._prev_position = prev_position

    @property
    def resources(self):
        """Gets the resources of this Ship.  # noqa: E501


        :return: The resources of this Ship.  # noqa: E501
        :rtype: Resources
        """
        return self._resources

    @resources.setter
    def resources(self, resources):
        """Sets the resources of this Ship.


        :param resources: The resources of this Ship.  # noqa: E501
        :type: Resources
        """
        if resources is None:
            raise ValueError("Invalid value for `resources`, must not be `None`")  # noqa: E501

        self._resources = resources

    @property
    def command(self):
        """Gets the command of this Ship.  # noqa: E501


        :return: The command of this Ship.  # noqa: E501
        :rtype: Command
        """
        return self._command

    @command.setter
    def command(self, command):
        """Sets the command of this Ship.


        :param command: The command of this Ship.  # noqa: E501
        :type: Command
        """

        self._command = command

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(Ship, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, Ship):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other