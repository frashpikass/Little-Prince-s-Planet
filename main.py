#! /usr/bin/env python
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL.Image import *

# ------------------------------
# GLOBAL CONSTANTS AND VARIABLES
# ------------------------------

# Rotation variables: define the main rotation speed for elements in the scene
zrot = 0.0
delta_rot = 0.05

# Properties for the Sky Dome
# Radius and center
distance_limit = 100
sky_radius = distance_limit / 3
sky_center = [0.0, 0.0, 0.0]

# How fast the skybox turns on its axis, it's a multiplier for zrot
sky_rotation_factor = 0.1

# A multiplier for sky_radius to define how far the star should be from the galaxy center
star_distance = 0.7

# Safety radius: the observer can't escape this boundary. Max distance from the "sky dome center"
safety_radius = sky_radius * 2 / 3

# Planet and satellite radius, tilt, orbit planes, speed modifiers...
planet_radius = 1.3
planet_tilt = 25
satellite_angle_of_orbit = 25
satellite_radius = 0.3
satellite_distance_from_planet_center = 4
satellite_angular_speed_modifier = -3

# Camera (eye) position, direction (also with phi and theta angles for direction and tilt)
phi = 0.0
theta = 0.0
eye = [0.0, 0.0, 8.0]
eye_direction = [0.0, 5.0, 50.0]
# Grain of camera turning
eye_rotation_delta = 5

# Initial window size
width = 800
height = 600


# ---------------
# UTILITY METHODS
# ---------------


def set_safe_eye_position(new_position):
    """
    Sets the eye position to new_position if it's within sky boundaries
    :param new_position: an array of three elements, the new eye position
    :return: true if the new position is within boundaries, false otherwise
    """
    global eye
    distance_of_new_position_from_sky_center = math.sqrt(
        (new_position[0] - sky_center[0]) ** 2
        + (new_position[1] - sky_center[1]) ** 2
        + (new_position[2] - sky_center[2]) ** 2
    )

    if distance_of_new_position_from_sky_center <= safety_radius:
        eye = new_position
        glutPostRedisplay()
        return True
    else:
        return False


def load_texture(fn, has_alpha):
    """
    Load a texture from a position, generates a valid OpenGL texture object
    :rtype: Texture
    :param fn: texture file name
    :param has_alpha: True if texture has alpha channel
    :return: a valid OpenGL texture object
    """

    image = open(fn)

    ix = image.size[0]
    iy = image.size[1]
    if has_alpha:
        image = image.tobytes("raw", "RGBA", 0, -1)
    else:
        image = image.tobytes("raw", "RGBX", 0, -1)

    # Create Texture
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)  # 2d texture (x and y size)

    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

    if has_alpha:
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
    else:
        glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)

    # set the texture's minification properties (mapping textures to bigger areas)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    # set the texture's stretching properties (mapping textures to smaller areas)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

    return texture


def position_on_sphere(
        sphere_center,
        dest_longitude,
        dest_latitude,
        dest_height,
        dest_orientation
):
    """
    Position the reference system over a destination point on a sphere.
    The y axis will correspond to the normal of the sphere at the point.
    The x axis will be orthogonal to the y axis at a specific orientation.
    The z axis will be orthogonal to the x-y plane

    :param sphere_center: vector of three coordinates, center of the sphere
    :param dest_longitude: longitude of the point on the sphere's surface
    (horizontal angle from the first meridian, in degrees)
    :param dest_latitude: latitude of the point on the sphere's surface
    (vertical angle from the equator, in degrees)
    :param dest_height: distance of the point from the sphere center
    :param dest_orientation: orientation of the final reference system
    :return: nothing
    """

    # 1) Move to the sphere center
    glTranslatef(
        sphere_center[0],
        sphere_center[1],
        sphere_center[2]
    )

    # 2) Rotate around y by a degree of longitude - 90
    glRotatef(dest_longitude - 90, 0.0, 1.0, 0.0)

    # 3) Rotate around z by a degree of latitude - 90
    glRotatef(dest_latitude - 90, 0.0, 0.0, 1.0)

    # 4) Translate the reference system up to the desired height
    glTranslatef(
        0.0,
        dest_height,
        0.0
    )

    # 5) Perform the final rotation around y to set the final orientation
    glRotatef(dest_orientation, 0.0, 1.0, 0.0)


def init(width, height):  # We call this right after our OpenGL window is created.
    """
    General OpenGL initialization function. Sets all the initial parameters.
    :param width: width of the window
    :param height: height of the window
    :return:
    """
    global quadratic, earth_texture, sky_texture, glass_texture, star_texture
    global planet_texture, rose_texture, baobab_texture, prince_texture, pizza_texture

    # Enables Depth Testing.
    # Makes 3D drawing work when something is in front of something else
    glEnable(GL_DEPTH_TEST)

    # Enable smooth shading
    glShadeModel(GL_SMOOTH)

    earth_texture = load_texture("textures/earth.jpg", has_alpha=False)
    star_texture = load_texture("textures/star.jpg", has_alpha=False)
    sky_texture = load_texture("textures/sky.png", has_alpha=False)
    planet_texture = load_texture("./textures/moon.png", has_alpha=False)
    rose_texture = load_texture("./textures/rose_nocup.png", has_alpha=True)
    baobab_texture = load_texture("./textures/baobab.png", has_alpha=True)
    prince_texture = load_texture("./textures/lp.png", has_alpha=True)
    pizza_texture = load_texture("./textures/pizza.png", has_alpha=False)
    glass_texture = load_texture("./textures/glass.png", has_alpha=True)

    # Set up quadric and its normals for correct light shading
    quadratic = gluNewQuadric()
    gluQuadricNormals(quadratic, GLU_SMOOTH)  # Create Smooth Normals (NEW)
    gluQuadricTexture(quadratic, GL_TRUE)  # Create Texture Coords (NEW)

    glEnable(GL_TEXTURE_2D)

    glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)
    glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)

    # Set The Projection Matrix
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Calculate The Aspect Ratio Of The Window and set maximum draw distance
    gluPerspective(45.0, float(width) / float(height), 0.1, 5 * distance_limit)

    # Back to model view matrix
    glMatrixMode(GL_MODELVIEW)


# ---------
# CALLBACKS
# ---------


def display():
    """
    A callback to display graphics. Draws the whole 3D scene
    :return: nothing
    """
    global eye_direction
    global zrot, texture, quadratic, earth_texture

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear The Screen And The Depth Buffer

    # Set the default color for color buffers
    glClearColor(1.0, 1.0, 1.0, 1.0)

    # Reset the position
    glLoadIdentity()

    # Set the camera (eye) position and direction
    eye_direction = (
        eye[0] - math.sin(theta * 2 * math.pi / 360.0),
        eye[1] + math.sin(phi * 2 * math.pi / 360),
        eye[2] - math.cos(theta * 2 * math.pi / 360.0)
    )
    gluLookAt(
        eye[0], eye[1], eye[2],
        eye_direction[0], eye_direction[1], eye_direction[2],
        0.0, 1.0, 0.0
    )

    # Setup the lights
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)  # Enable lighting
    glEnable(GL_LIGHT0)  # Enable light #0
    glEnable(GL_NORMALIZE)  # Automatically normalize normals

    # Draw the sky dome
    draw_sky()

    # Draw the star and its light
    draw_starlight()

    # Draw the planet at the center of the scene
    draw_planet()

    # Increase z rotation of all rotating bodies (planet, satellite, sky dome, star...)
    zrot += delta_rot

    #  Since this is double buffered, swap the buffers to display what just got drawn.
    glutSwapBuffers()


def resize_scene(width, height):
    """
    Resizes the whole scene and perspective as the windows size is changed
    :param width: new window width
    :param height: new window height
    :return:
    """
    if height == 0:  # Prevent A Divide By Zero If The Window Is Too Small
        height = 1

    glViewport(0, 0, width, height)  # Reset The Current Viewport And Perspective Transformation
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(width) / float(height), 0.1, 5 * distance_limit)
    glMatrixMode(GL_MODELVIEW)


def keyboard(key, x, y):
    """
    Callback which reads the currently pressed normal key from the keyboard and
    acts consequently.
    In particular, w, a, s, d move the eye position in the space
    :param key: The pressed key
    :param x: x mouse position
    :param y: y mouse position
    :return: nothing
    """

    global eye, theta, phi, eye_rotation_delta
    eye_new = eye[:]

    if key == chr(27):
        sys.exit()
    if key == 'w':  # move forward
        eye_new[0] -= math.sin(theta * 2 * math.pi / 360.0)  # radians conversion of angle theta
        eye_new[2] -= math.cos(theta * 2 * math.pi / 360.0)

    if key == 's':  # move back
        eye_new[0] += math.sin(theta * 2 * math.pi / 360.0)
        eye_new[2] += math.cos(theta * 2 * math.pi / 360.0)

    if key == 'a':  # move left
        eye_new[0] -= math.cos(theta * 2 * math.pi / 360.0)
        eye_new[2] += math.sin(theta * 2 * math.pi / 360.0)

    if key == 'd':  # move right
        eye_new[0] += math.cos(theta * 2 * math.pi / 360.0)
        eye_new[2] -= math.sin(theta * 2 * math.pi / 360.0)

    set_safe_eye_position(eye_new)
    return


def special_pressed(key, x, y):
    """
    Callback which reads the currently pressed special key from the keyboard and
    acts consequently.
    In particular, arrow keys move the eye direction in space

    :param key: The pressed key
    :param x: x mouse position
    :param y: y mouse position
    :return: nothing
    """

    global theta, eye_rotation_delta, phi
    if key == GLUT_KEY_RIGHT:  # look right
        theta = (theta - eye_rotation_delta) % 360
        glutPostRedisplay()
        return
    if key == GLUT_KEY_LEFT:  # look left
        theta = (theta + eye_rotation_delta) % 360
        glutPostRedisplay()
        return
    if key == GLUT_KEY_UP:  # look up
        if phi < 90:
            phi += eye_rotation_delta
        glutPostRedisplay()
        return
    if key == GLUT_KEY_DOWN:  # look down
        if phi > -90:
            phi -= eye_rotation_delta
        glutPostRedisplay()
        return


# ---------------------------
# MATERIAL DEFINITION METHODS
# ---------------------------


def load_planet_material():
    """
    Loads a good material to represent the planet
    :return: nothing
    """
    # Set the material
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [10, 10, 10, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [5, 5, 5, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [0, 0, 0, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 70.0)


def load_dull_material():
    """
    Loads a good material to represent objects with a matte texture that doesn't reflect light
    :return:
    """
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [1, 1, 1, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
    glMaterialfv(GL_FRONT, GL_SHININESS, 10)
    glMaterialfv(GL_BACK, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
    glMaterialfv(GL_BACK, GL_DIFFUSE, [0.1, 0.1, 0.1, 1.0])
    glMaterialfv(GL_BACK, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])
    glMaterialfv(GL_BACK, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
    glMaterialfv(GL_BACK, GL_SHININESS, 0)


def load_shiny_material():
    """
    Loads a good material to represent objects with a polished texture that reflects light
    :return: nothing
    """
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.1, 0.1, 0.1, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.95, 0.95, 0.95, 0.6])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [10, 10, 10, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [0.0, 0.0, 0.0, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, 120)


def load_glowing_material():
    """
    Loads a good material to represent objects which glow
    :return: nothing
    """
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0, 0, 0, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [20, 20, 20, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [5, 5, 5, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, [1000.0, 1000.0, 1000.0, 0.3])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, 128)

# ---------------
# DRAWING METHODS
# ---------------


def draw_crossed_textures(longitude, latitude, height, w, h, texture, faces):
    """
    Draws a texture with alpha channel (transparency) over a star of rectangles, to mimic a 3D object.
    The object is drawn on the surface of the main planet
    over the spot specified by longitude, latitude and height.
    :param longitude: horizontal angle from the fundamental meridian
    :param latitude: vertical angle from the equator
    :param height: height from the planet centre
    :param w: width of the rectangles
    :param h: height of the rectangles
    :param texture: a texture with alpha channel (transparency)
    :param faces: number of faces to represent
    :return: nothing
    """
    # Save original position
    glPushMatrix()

    # Get on the right spot on the planet
    position_on_sphere(
        sky_center,
        longitude, latitude, height, 0
    )

    # Enable alpha blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.0)

    # Load correct texture
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glBindTexture(GL_TEXTURE_2D, texture)

    # Map the texture to a rectangle of width w and height h

    turn = 180 / faces

    for i in range(turn, 181, turn):
        # Start drawing a rectangle and define its normal
        glPushMatrix()
        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)

        # Map the corners of the rectangle to the texture
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-(w / 2), 0.0, 0.0)

        glTexCoord2f(1.0, 0.0)
        glVertex3f((w / 2), 0.0, 0.0)

        glTexCoord2f(1.0, 1.0)
        glVertex3f((w / 2), h, 0.0)

        glTexCoord2f(0.0, 1.0)
        glVertex3f(-(w / 2), h, 0.0)

        # End the rectangle drawing and mapping
        glEnd()
        glPopMatrix()

        # Rotate the reference system to draw the next face
        glRotatef(i, 0.0, 1.0, 0.0)

    # Disable alpha blending
    glDisable(GL_ALPHA_TEST)
    glDisable(GL_BLEND)

    # Back to original position
    glPopMatrix()


def draw_sky():
    """
    Draw the sky dome
    :return:
    """
    # Disable the lighting so that the sky is always visible and doesn't change in accordance with light sources
    glDisable(GL_LIGHTING)

    glPushMatrix()  # 1: context for the turning sky

    # Disable depth mask, enable texturing
    glDepthMask(GL_FALSE)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_TEXTURE_GEN_T)
    glBindTexture(GL_TEXTURE_2D, sky_texture)

    # Rotate the texture and the sky dome
    glTranslatef(0.0, 0.0, 0.0)
    glRotatef(90, 1.0, 0.0, 0.0)
    glRotatef(sky_rotation_factor * zrot, 0.0, 0.1, 1.0)

    # Draw the sky dome
    gluSphere(quadratic, sky_radius, 64, 64)

    # Disable texturing and re-enable depth mask
    glDisable(GL_TEXTURE_GEN_S)
    glDisable(GL_TEXTURE_GEN_T)
    glDepthMask(GL_TRUE)

    glPopMatrix()  # 1: context for the turning sky

    # Re-enable lighting
    glEnable(GL_LIGHTING)


def draw_starlight():
    """
    Draws a star, which also doubles as a diffuse light source
    :return:
    """
    # We start from the sky centre

    # Set light parameters
    # This is the diffuse component of the point-shaped light source.
    # It irradiates in all directions
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (8.0, 8.0, 8.0, 1))

    # This is the ambient component of the light source. It illuminates dark polygons
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.1, 0.2, 0.4, 0.5))

    # This is the specular component of the light source. It generates reflections on specular materials
    glLightfv(GL_LIGHT0, GL_SPECULAR, [8, 8, 9, 1.0])

    # Light up polygons in a different way if they are illuminated from the front face or the back face
    glLightModelf(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)

    # Set the light that points towards the center of the galaxy, but somewhere far away in the distance

    glPushMatrix()  # 1: Move to an orbit fixed within the sky

    position_on_sphere(sky_center, -sky_rotation_factor * zrot, 0, sky_radius * star_distance, 0)
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 0, 0, 1])

    # Lights off, so that the star can be painted
    glDisable(GL_LIGHTING)

    glDepthMask(GL_FALSE)
    glPushMatrix()  # 2: star rotation context

    # Load the star material
    load_glowing_material()

    glEnable(GL_TEXTURE_2D)
    glEnable(GL_TEXTURE_GEN_T)
    glBindTexture(GL_TEXTURE_2D, star_texture)
    glTranslatef(0.0, 0.0, 0.0)
    glRotatef(2 * zrot, 0, 0.0, 1.0)

    # Draw the star
    gluSphere(quadratic, planet_radius, 32, 32)
    glPopMatrix()  # 2: star rotation context
    glDisable(GL_TEXTURE_GEN_S)
    glDisable(GL_TEXTURE_GEN_T)
    glDepthMask(GL_TRUE)

    # Lights back on
    glEnable(GL_LIGHTING)

    glPopMatrix()  # 1: Move back to the sky centre


def draw_planet():
    """
    Draw the planet and its decorations
    :return: nothing
    """

    glPushMatrix()  # 1: planet tilt and rotate

    # Planet tilt
    glRotatef(planet_tilt, 0.0, 0.0, 1.0)

    # Draw the satellite
    glPushMatrix()  # 2: satellite rotation
    # Rotate the scene to change the angle of the orbit plane for the satellite
    glRotatef(satellite_angle_of_orbit, 0.0, 0.0, 1.0)
    draw_satellite(0, satellite_angular_speed_modifier * zrot, satellite_distance_from_planet_center)
    glPopMatrix()  # 2: satellite rotation

    # Texture tilt
    glRotatef(90.0, 1.0, 0.0, 0.0)

    # Rotate the planet On its rotation Axis
    glRotatef(zrot, 0.0, 0.0, 1.0)

    # Set the material
    load_planet_material()

    # Enable mapping
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_TEXTURE_GEN_T)
    glBindTexture(GL_TEXTURE_2D, planet_texture)

    # Draw the planet and stop texturing
    gluSphere(quadratic, planet_radius, 64, 64)
    glDisable(GL_TEXTURE_GEN_S)
    glDisable(GL_TEXTURE_GEN_T)

    # Draw the Little prince on the planet pole
    draw_little_prince(180, 0, planet_radius - 0.1, w=0.7, h=1.2)

    # Draw the Rose (it's done here to correctly render transparency)
    draw_rose(60, 30, planet_radius - 0.1, w=0.5, h=0.8)

    # Draw the baobab
    draw_baobab(-60, -30, planet_radius - 0.1, w=2, h=3)

    glPopMatrix()  # 1: planet tilt and rotate


def draw_satellite(longitude, latitude, height):
    """
    Draws a satellite of the main planet, positioned over the specific coordinates
    (using the planet as a reference) and at the specific height from the planet
    centre.

    :param longitude: horizontal angle from the fundamental meridian
    :param latitude: vertical angle from the equator
    :param height: height from the planet centre
    :return: nothing
    """
    # Setup the correct material to draw the planet
    load_planet_material()

    # Get to the right position
    glPushMatrix()  # 1: Saving the original position
    position_on_sphere(
        sky_center,
        longitude, latitude, height, 0
    )

    # Satellite axis rotation
    glRotatef(zrot, 0.0, 0.0, 1.0)

    # Texturing
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_TEXTURE_GEN_T)
    glBindTexture(GL_TEXTURE_2D, earth_texture)

    # Drawing the sphere
    gluSphere(quadratic, satellite_radius, 64, 64)

    # Disabling texture mapping
    glDisable(GL_TEXTURE_GEN_S)
    glDisable(GL_TEXTURE_GEN_T)
    glPopMatrix()   # 1: Back to the original position


def draw_little_prince(longitude, latitude, height, w, h):
    """
    Draw the Little Prince on the planet at specified coordinates and height, and with a specific size
    :param longitude: horizontal angle from the fundamental meridian
    :param latitude: vertical angle from the equator
    :param height: height from the planet centre
    :param w: width of the drawn element
    :param h: height of the drawn element
    :return: nothing
    """
    # Set the material
    load_shiny_material()

    # Draw
    draw_crossed_textures(longitude, latitude, height, w, h, prince_texture, 1)


def draw_rose(longitude, latitude, height, w, h):
    """
    Draw a rose on the planet at specified coordinates and height, and with a specific size
    :param longitude: horizontal angle from the fundamental meridian
    :param latitude: vertical angle from the equator
    :param height: height from the planet centre
    :param w: width of the drawn element
    :param h: height of the drawn element
    :return: nothing
    """
    # Load the correct material for the rose
    load_dull_material()

    # draw the rose
    draw_crossed_textures(longitude, latitude, height, w, h, rose_texture, 10)

    # draw the cup over the rose
    glPushMatrix()  # 1: saving the position at the base of the rose
    # Get on the right spot over the planet
    position_on_sphere(
        sky_center,
        longitude, latitude, height, 0
    )

    # Rotation to correctly position the cylinder as orthogonal to the planet
    glRotatef(-90, 1.0, 0.0, 0.0)

    # Set up the glass like material
    load_shiny_material()

    # Enable alpha blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.0)

    # Load the correct texture for the glass like material
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glBindTexture(GL_TEXTURE_2D, glass_texture)

    # Draw the glass bowl
    gluCylinder(quadratic, w, w, 3 * h / 4, 64, 64)
    glTranslatef(0.0, 0.0, 3 * h / 4)
    gluCylinder(quadratic, w, w / 7, h / 2, 32, 32)

    # Disable alpha blending
    glDisable(GL_ALPHA_TEST)
    glDisable(GL_BLEND)

    # End
    glPopMatrix()


def draw_baobab(longitude, latitude, height, w, h):
    """
    Draw a baobab on the planet at specified coordinates and height, and with a specific size
    :param longitude: horizontal angle from the fundamental meridian
    :param latitude: vertical angle from the equator
    :param height: height from the planet centre
    :param w: width of the drawn element
    :param h: height of the drawn element
    :return: nothing
    """

    # Set the material
    load_dull_material()

    # Draw
    draw_crossed_textures(longitude, latitude, height, w, h, baobab_texture, 4)


# ----------
# MAIN BLOCK
# ----------


def main():
    """
    Main function
    :return: nothing
    """
    glutInit()

    # Select type of Display mode:
    # Double buffer
    # RGBA color
    # Alpha components supported
    # Depth buffer
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

    # Open a window of the correct size
    glutInitWindowSize(width, height)

    # The window starts at the upper left corner of the screen
    glutInitWindowPosition(100, 100)
    glutCreateWindow("Little Prince's Lair")

    # Register the drawing function with glut, BUT in Python land, at least using PyOpenGL, we need to
    # set the function pointer and invoke a function to actually register the callback, otherwise it
    # would be very much like the C version of the code.
    glutDisplayFunc(display)

    # Uncomment this line to get full screen.
    # glutFullScreen()

    # When we are doing nothing, redraw the scene.
    glutIdleFunc(display)

    # Register the function called when our window is resized.
    glutReshapeFunc(resize_scene)

    # Register the function called when the keyboard is pressed.
    glutKeyboardFunc(keyboard)

    # Register the function called when the keyboard is pressed.
    glutSpecialFunc(special_pressed)

    # Initialize our window.
    init(width, height)

    # Start Event Processing Engine
    glutMainLoop()


# In case it was loaded from console, these lines of code bootstraps the main function
if __name__ == "__main__":
    print("WASD move the observer in space.")
    print("Arrow keys change the camera direction.")
    print("Hit ESC key to quit.")

    # Call the main function
    main()
