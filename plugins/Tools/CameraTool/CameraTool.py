# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from UM.Tool import Tool
from UM.Event import Event, MouseEvent, KeyEvent
from UM.Math.Vector import Vector
from UM.Math.Matrix import Matrix
from UM.Application import Application
from PyQt5 import QtCore, QtWidgets

import math

##  Provides the tool to manipulate the camera: moving, zooming and rotating
#
#   Note that zooming is performed by moving closer to or further away from the origin ("dolly")
#   instead of changing the field of view of the camera ("zoom")

class CameraTool(Tool):
    def __init__(self):
        super().__init__()
        self._scene = Application.getInstance().getController().getScene()

        self._yaw = 0
        self._pitch = 0
        self._origin = Vector(0, 0, 0)
        self._min_zoom = 0
        self._max_zoom = 2000.0
        self._manual_zoom = 200

        self._rotate = False
        self._move = False
        self._dragged = False

        self._shift_is_active = None
        self._ctrl_is_active = None
        self._space_is_active = None

        self._start_drag = None
        self._start_y = None

        self._drag_distance = 0.05

    ##  Set the minumum and maximum distance from the origin used for "zooming" the camera
    #
    #   \param min type(float) distance from the origin when fully zoomed in
    #   \param max type(float) distance from the origin when fully zoomed out
    def setZoomRange(self, min, max):
        self._min_zoom = min
        self._max_zoom = max

    ##  Set the point around which the camera rotates
    #
    #   \param origin type(Vector) origin point
    def setOrigin(self, origin):
        translation = origin - self._origin
        self._origin = origin
        self._scene.getActiveCamera().translate(translation)
        self._rotateCamera(0.0, 0.0)

    ##  Get the point around which the camera rotates
    #
    #   \return type(Vector) origin point
    def getOrigin(self):
        return self._origin

    ##  Prepare modifier-key variables on each event
    #
    #   \param event type(Event) event passed from event handler
    def checkModifierKeys(self, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        self._shift_is_active = modifiers == QtCore.Qt.ShiftModifier
        self._ctrl_is_active = modifiers == QtCore.Qt.ControlModifier
        #checks for the press and release event of the space key
        if event.type is Event.KeyPressEvent:
            if event.key == KeyEvent.SpaceKey:
                self._space_is_active = True
        if event.type is Event.KeyReleaseEvent:
            if event.key == KeyEvent.SpaceKey:
                self._space_is_active = False

    ##  Check if the event warrants a call off the _moveCamera method
    #
    #   \param event type(Event) event passed from event handler
    #   \return type(boolean)
    def moveEvent(self, event):
        if MouseEvent.MiddleButton in event.buttons: #mousewheel
            return True
        elif MouseEvent.LeftButton in event.buttons and self._shift_is_active is True: #shift -> leftbutton
            return True
        elif MouseEvent.RightButton in event.buttons and self._shift_is_active is True: #shift -> rightbutton
            return True

    ##  Check if the event warrants a call off the _rotateCamera method
    #
    #   \param event type(Event) event passed from event handler
    #   \return type(boolean)
    def rotateEvent(self, event):
        if MouseEvent.RightButton in event.buttons: #rightbutton
            return True
        elif MouseEvent.LeftButton in event.buttons and self._space_is_active is True: #shift -> leftbutton
            return True

    ##  Calls the zoomaction method for the mousewheel event, mouseMoveEvent (in combo with alt or space) and when the plus or minus keys are used
    #
    #   \param event type(Event) event passed from event handler
    #   \return type(boolean)
    def initiateZoom(self, event):
        if event.type is event.MousePressEvent:
            return False
        elif event.type is Event.MouseMoveEvent and self._space_is_active is True: #space -> mousemove
                if self._start_y == None:
                    self._start_y = event.y
                _diff_y = self._start_y - event.y
                if _diff_y != 0.0:
                    _zoom_speed = 2000
                    self._zoomCamera(_diff_y * _zoom_speed)
                    self._start_y = None
        elif event.type is Event.MouseWheelEvent:
            self._zoomCamera(event.vertical)
            return True
        elif event.type is Event.KeyPressEvent:
            if event.key == KeyEvent.MinusKey or event.key == KeyEvent.UnderscoreKey: #checks for both the minus and underscore key because they usually share a button on the keyboard and are sometimes interchanged
                self._zoomCamera(-(self._manual_zoom))
                return True
            elif event.key == KeyEvent.PlusKey or event.key == KeyEvent.EqualKey: #same story as the minus and underscore key: it checks for both the plus and equal key (so you won't have to do shift -> equal, to use the plus-key)
                self._zoomCamera(self._manual_zoom)
                return True

    ##  Handle mouse and keyboard events
    #
    #   \param event type(Event)
    def event(self, event):
        self.checkModifierKeys(event)
        # handle mouse- and keyboard-initiated zoom-events
        self.initiateZoom(event)

        # handle keyboard-initiated rotate-events
        if event.type is event.KeyPressEvent and not self._ctrl_is_active:
            if event.key == KeyEvent.UpKey:
                self._rotateCamera(0, 0.01)
            if event.key == KeyEvent.DownKey:
                self._rotateCamera(0, -0.01)
            if event.key == KeyEvent.RightKey:
                self._rotateCamera(-0.01, 0)
            if event.key == KeyEvent.LeftKey:
                self._rotateCamera(0.01, 0)

        # handle mouse-initiated rotate- and move-events
        if event.type is Event.MousePressEvent:
            if self.moveEvent(event) == True:
                self._move = True
                self._start_drag = (event.x, event.y)
                return True
            elif self.rotateEvent(event) == True:
                self._rotate = True
                self._start_drag = (event.x, event.y)
                return True

        elif event.type is Event.MouseMoveEvent:
            if self._rotate or self._move:
                diff = (event.x - self._start_drag[0], event.y - self._start_drag[1])
                length_squared = diff[0] * diff[0] + diff[1] * diff[1]

                if length_squared > (self._drag_distance * self._drag_distance):
                    if self._rotate:
                        self._rotateCamera(event.deltaX, event.deltaY)
                        self._dragged = True
                        return True
                    elif self._move:
                        self._moveCamera(event)
                        self._dragged = True
                        return True

        elif event.type is Event.MouseReleaseEvent:
            if self._rotate or self._move:
                self._rotate = False
                self._move = False
                self._start_drag = None
            if self._dragged:
                self._dragged = False
                return True

        return False

    ##  Move the camera in response to a mouse event.
    #
    #   \param event type(Event) event passed from event handler
    def _moveCamera(self, event):
        camera = self._scene.getActiveCamera()
        if not camera or not camera.isEnabled():
            return

        self._scene.acquireLock()

        camera_position = camera.getWorldPosition()
        camera.translate(Vector(-event.deltaX * 100, event.deltaY * 100, 0))
        translation = camera.getWorldPosition() - camera_position
        self._origin += translation

        self._scene.releaseLock()

    ##  "Zoom" the camera in response to a mouse event.
    #
    #   Note that the camera field of view is left unaffected, but instead the camera moves closer to the origin
    #   \param zoom_range type(int) factor by which the distance to the origin is multiplied, multiplied by 1280
    def _zoomCamera(self, zoom_range):
        camera = self._scene.getActiveCamera()
        if not camera or not camera.isEnabled():
            return

        self._scene.acquireLock()

        r = (camera.getWorldPosition() - self._origin).length()
        delta = r * (zoom_range / 128 / 10.0)
        r -= delta
        if delta > 0:
            if r > self._min_zoom:
                camera.translate(Vector(0.0, 0.0, -delta))
        else:
            if r < self._max_zoom:
                camera.translate(Vector(0.0, 0.0, -delta))

        self._scene.releaseLock()

    ##  Rotate the camera in response to a mouse event.
    #
    #   \param x type(int) amount by which the camera should be rotated horizontally, expressed in pixelunits
    #   \param y type(int) amount by which the camera should be rotated vertically, expressed in pixelunits
    def _rotateCamera(self, x, y):
        camera = self._scene.getActiveCamera()
        if not camera or not camera.isEnabled():
            return

        self._scene.acquireLock()

        dx = math.radians(x * 180.0)
        dy = math.radians(y * 180.0)

        diff = camera.getPosition() - self._origin
        my = Matrix()
        my.setByRotationAxis(dx, Vector.Unit_Y)

        mx = Matrix(my.getData())
        mx.rotateByAxis(dy, Vector.Unit_Y.cross(diff).normalized())

        n = diff.multiply(mx)

        try:
            angle = math.acos(Vector.Unit_Y.dot(n.normalized()))
        except ValueError:
            return

        if angle < 0.1 or angle > math.pi - 0.1:
            n = diff.multiply(my)

        n += self._origin

        camera.setPosition(n)
        camera.lookAt(self._origin)

        self._scene.releaseLock()
