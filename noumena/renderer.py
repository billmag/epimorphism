from ctypes import *
from OpenGL.GL import *
from OpenGL.GLUT import *

from phenom.keyboard import *
from phenom.mouse import *

import common.util.glFreeType

class Renderer():

    FONT_PATH = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"

    def __init__(self, profile, state):

        # set variables
        self.profile, self.state = profile, state

        # initialize glut
        glutInit(1, [])

        # create window
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA)

        if(self.profile.full_screen):
            glutGameModeString(str(self.profile.viewport_width) + "x" +
                               str(self.profile.viewport_height) + ":24@" +
                               str(self.profile.viewport_refresh))
            glutEnterGameMode()

        else:
            glutInitWindowSize(self.profile.viewport_width, self.profile.viewport_height)
            glutInitWindowPosition(10, 10)
            glutCreateWindow("Epimorphism")

        self.reshape(self.profile.viewport_width, self.profile.viewport_height)

        # register callbacks
        glutReshapeFunc(self.reshape)

        # generate buffer object
        size = (self.profile.kernel_dim ** 2) * 4 * sizeof(c_float)
        self.pbo = GLuint()

        glGenBuffers(1, byref(self.pbo))
        glBindBuffer(GL_ARRAY_BUFFER, self.pbo)
        empty_buffer = (c_float * (sizeof(c_float) * 4 * self.profile.kernel_dim ** 2))()
        glBufferData(GL_ARRAY_BUFFER, size, empty_buffer, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        # generate texture
        self.display_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.display_tex)

        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, self.profile.kernel_dim, self.profile.kernel_dim,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # init gl
        glEnable(GL_TEXTURE_2D)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_FASTEST)
        glShadeModel(GL_FLAT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # fps data
        self.d_time_start = self.d_time = self.d_timebase = 0
        self.frame_count = 0.0

        # misc variables
        self.console = False
        self.show_fps = False
        self.fps_font_size = 16
        self.fps_width = 100
        self.font = common.util.glFreeType.font_data(self.FONT_PATH, self.fps_font_size)


    def __del__(self):

        glBindBuffer(GL_ARRAY_BUFFER, self.pbo)
        glDeleteBuffers(1, self.pbo)


    def register_callbacks(self, keyboard, mouse, motion, render_console, console_keyboard):
        self.keyboard = keyboard
        glutKeyboardFunc(keyboard)
        glutSpecialFunc(keyboard)
        glutMouseFunc(mouse)
        glutMotionFunc(motion)
        self.render_console = render_console
        self.console_keyboard = console_keyboard


    def set_inner_loop(self, inner_loop):
        glutDisplayFunc(inner_loop)


    def toggle_console(self):
        self.console = not self.console
        if(self.console):
            glutKeyboardFunc(self.console_keyboard)
            glutSpecialFunc(self.console_keyboard)
        else:
            glutSpecialFunc(self.keyboard)
            glutKeyboardFunc(self.keyboard)


    def toggle_fps(self):
        self.show_fps = not self.show_fps


    def render_fps(self):
        dims = [-1.0 + 2.0 * self.fps_width / self.profile.viewport_width,
                1.0 - 2.0 * (10 + (self.fps_font_size + 4) * 2) / self.profile.viewport_height]

        dims_v = [0, self.profile.viewport_height]



        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

        glColor3ub(0xff, 0xff, 0xff)

        self.font.glPrint(6, dims_v[1] - self.fps_font_size - 6, "fps: %.2f" % (1000.0 / self.fps))
        self.font.glPrint(6, dims_v[1] - 2 * self.fps_font_size - 10, "avg: %.2f" % (1000.0 / self.fps_avg))


    def reset_fps_avg():
        self.d_time = 0


    def reshape(self, w, h):

        # set viewport
        self.profile.viewport_width = w
        self.profile.viewport_height = h
        self.aspect = float(w) / float(h)
        glViewport(0, 0, self.profile.viewport_width, self.profile.viewport_height)

        # configure projection matrix
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)


    def do(self):

        # compute frame rate
        if(self.d_time == 0):
            self.frame_count = 0
            self.d_time_start = self.d_time = self.d_timebase = glutGet(GLUT_ELAPSED_TIME)
        else:
            self.frame_count += 1
            self.d_time = glutGet(GLUT_ELAPSED_TIME)
            if(self.frame_count % self.profile.debug_freq == 0):
                self.fps = (1.0 * self.d_time - self.d_timebase) / self.profile.debug_freq
                self.fps_avg = (1.0 * self.d_time - self.d_time_start) / self.frame_count
                self.d_timebase = self.d_time

        # copy texture from pbo
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER_ARB, self.pbo)
        glBindTexture(GL_TEXTURE_2D, self.display_tex)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.profile.kernel_dim, self.profile.kernel_dim,
                        GL_RGBA, GL_UNSIGNED_BYTE, None)
        glBindBuffer(GL_PIXEL_PACK_BUFFER_ARB, 0)
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER_ARB, 0)

        # compute texture coordinates
        x0 = .5 - self.state.vp_scale / 2 - self.state.vp_center_x * self.aspect
        x1 = .5 + self.state.vp_scale / 2 - self.state.vp_center_x * self.aspect
        y0 = .5 - self.state.vp_scale / (2 * self.aspect) + self.state.vp_center_y
        y1 = .5 + self.state.vp_scale / (2 * self.aspect) + self.state.vp_center_y


        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

        # render texture
        glBegin(GL_QUADS)

        glTexCoord2f(x0, y0)
        glVertex3f(-1.0, -1.0, 0)
        glTexCoord2f(x1, y0)
        glVertex3f(1.0, -1.0, 0)
        glTexCoord2f(x1, y1)
        glVertex3f(1.0, 1.0, 0)
        glTexCoord2f(x0, y1)
        glVertex3f(-1.0, 1.0, 0)

        glEnd()

        # render console
        if(self.console):
            self.render_console()

        if(self.show_fps):
            self.render_fps()

        # repost
        glutSwapBuffers()
        glutPostRedisplay()


    def start(self):

        glutMainLoop()


