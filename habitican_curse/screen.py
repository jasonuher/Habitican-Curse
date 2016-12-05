""" Module "Screen" : Wrapper for the ncurses screen

    All screen related functions such as displaying text, colors, background,
    saving/restoring context etc. go here.
"""
# Standard Library Imports
import curses
import tempfile
import math
import threading

# Custom Module Imports
import config as C

#Set up logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug logging started for %s..." % __name__)

class Screen(object):

    def __init__(self, screen):
        self.fullscreen = screen
        self.screen = screen

        # These are special context registers.
        # Use these to store some important backtrack points.
        self.ctxts = []
        for i in xrange(C.NUM_CONTEXT_REGISTERS):
            self.ctxts += [tempfile.TemporaryFile()]

        self.active_registers = [False]*C.NUM_CONTEXT_REGISTERS

        # This is the stack for saving contexts.
        # Use these to get a proper order of backtrack points
        self.stackFile = tempfile.TemporaryFile()
        self.stack = []
        self.SCR_X=0
        self.SCR_Y=0
        self.SCR_MENU_ITEM_WIDTH=0

        self.lock = threading.RLock()

    ########################
    #                      #
    # Screen Functions     #
    #                      #
    ########################
    #Things related directly to habiticancurse

    def Initialize(self):

        #global SCR_X, SCR_Y, SCR_MENU_ITEM_WIDTH
        # Cursor not visible
        curses.curs_set(0)

        # Color and Background
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(C.SCR_COLOR_RED, curses.COLOR_RED, C.SCR_COLOR_BGRD)
        curses.init_pair(C.SCR_COLOR_CYAN, curses.COLOR_CYAN, C.SCR_COLOR_BGRD)
        curses.init_pair(C.SCR_COLOR_GREEN, curses.COLOR_GREEN, C.SCR_COLOR_BGRD)
        curses.init_pair(C.SCR_COLOR_YELLOW, curses.COLOR_YELLOW, C.SCR_COLOR_BGRD)
        curses.init_pair(C.SCR_COLOR_MAGENTA, curses.COLOR_MAGENTA, C.SCR_COLOR_BGRD)
        curses.init_pair(C.SCR_COLOR_BLUE, curses.COLOR_BLUE, C.SCR_COLOR_BGRD)
        curses.init_pair(C.SCR_COLOR_WHITE, curses.COLOR_WHITE, C.SCR_COLOR_BGRD)

        curses.init_pair(C.SCR_COLOR_LIGHT_ORANGE, 209, C.SCR_COLOR_BGRD)
        curses.init_pair(C.SCR_COLOR_DARK_ORANGE, 208, C.SCR_COLOR_BGRD)
        curses.init_pair(C.SCR_COLOR_DARK_GRAY, 237, C.SCR_COLOR_BGRD)
        curses.init_pair(C.SCR_COLOR_LIGHT_GRAY, 244, C.SCR_COLOR_BGRD)

        curses.init_pair(C.SCR_COLOR_RED_GRAY_BGRD, curses.COLOR_RED, 234)
        curses.init_pair(C.SCR_COLOR_WHITE_GRAY_BGRD, curses.COLOR_WHITE, 234)
        curses.init_pair(C.SCR_COLOR_GREEN_GRAY_BGRD, curses.COLOR_GREEN, 234)
        curses.init_pair(C.SCR_COLOR_YELLOW_GRAY_BGRD, curses.COLOR_YELLOW, 234)
        curses.init_pair(C.SCR_COLOR_BLUE_GRAY_BGRD, curses.COLOR_BLUE, 234)
        curses.init_pair(C.SCR_COLOR_MAGENTA_GRAY_BGRD, curses.COLOR_MAGENTA, 234)

        curses.init_pair(C.SCR_COLOR_WHITE_GRAY_BGRD, curses.COLOR_WHITE, 234)
        curses.init_pair(C.SCR_COLOR_GRAY_WHITE_BGRD, 236, curses.COLOR_WHITE)


        self.SCR_Y, self.SCR_X = self.screen.getmaxyx()

        # The target global screen layout is this
        # |-- Display bar-------------------------------------|
        # +---------------------------------------------------+
        # |                                                   |
        # |           Items screen                            |
        # |                                                   |
        # |                                                   |
        # +---------------------------------------------------+
        # +---------------------------------------------------+
        # |                                                   |
        # |   Details Screen                                  |
        # |                                                   |
        # |                                                   |
        # +---------------------------------------------------+
        # |-- Stats bar --------------------------------------|
        # |-- command Bar--- ---------------------------------|
        self.status_display  = curses.newwin(1,self.SCR_X,          0,0)
        self.screen_items    = curses.newwin(self.SCR_Y-3,self.SCR_X, 1,0)
        #self.screen_details = curses.newwin(15,self.SCR_Y,15,0)
        self.bar_attr        = curses.newwin(1,self.SCR_X,          self.SCR_Y-2,0)
        self.bar_cmd         = curses.newwin(1,self.SCR_X,          self.SCR_Y-1,0)

        self.screen = self.screen_items

        # Same as writing " " in white on a black background
        self.screen.bkgd(' ', curses.color_pair(C.SCR_COLOR_WHITE))
        self.bar_attr.bkgd(' ',curses.color_pair(C.SCR_COLOR_WHITE_GRAY_BGRD))
        self.bar_cmd.bkgd(' ',curses.color_pair(C.SCR_COLOR_WHITE))

        # Screen Specifications
        self.SCR_Y, self.SCR_X = self.screen.getmaxyx()
        self.SCR_MENU_ITEM_WIDTH = (self.SCR_X - 10)/3

        # Test output
        self.status_display.addstr("Status Display")
        self.bar_attr.addstr("(stats bar)")
        self.bar_cmd.addstr("(command bar)")
        self.status_display.refresh()
        self.bar_attr.refresh()
        self.bar_cmd.refresh()

    #Send a status message to the top br
    def write_status_bar(self,string):

        self.Lock()

        try:
            self.status_display.erase()
            self.status_display.addstr(string)
            if string is not " ":
                logger.debug("UPDATE - \"%s\"" % string)
        except curses.error:
            #This is probably a cursor error, safe to ignore it?
            logger.debug("Curses error: %s" % curses.ERR)
            pass

        self.status_display.refresh()
        self.Release()

    #Write a string to the user attribute bar
    def write_user_diff(self, string,offset, color):

        self.Lock()
        self.bar_attr.addstr(0,offset,string,curses.A_BOLD | curses.color_pair(color))
        self.bar_attr.refresh()
        self.Release()

    #Write a string to the user attribute bar
    def write_user_attribute(self, string,offset, color, window=None):
        if(window is None):
            window = self.bar_attr

        self.Lock()
        window.addstr(0,offset,string,curses.A_BOLD | curses.color_pair(color))
        window.refresh()
        self.Release()

    def clear_command_bar(self):
        self.bar_cmd.erase()
        self.bar_cmd.refresh()

    #Emulate the vim command line (the ':' command)
    #This shoud probably go into interface?
    def Command(self):
        logger.debug("Reading in a new command via :")
        self.Lock()

        self.bar_cmd.erase()
        self.bar_cmd.addstr(":")
        self.bar_cmd.refresh()

        curses.echo()
        curses.curs_set(1)
        read_string = ""

        cursor = 1
        while(cursor < C.SCR_Y):
            c = self.bar_cmd.getch(0, cursor)
            if c == ord('\n'): # Enter Key
                break
            elif c == 27:        # Escape Key
                self.Noecho()
                self.CursorHide()
                return ""
            elif c == curses.KEY_BACKSPACE or c == curses.KEY_DC or c == 127:
                cursor -= 1
                if cursor == 0:
                    self.Noecho()
                    self.CursorHide()
                    return ""

                read_string = read_string[:-1]
                self.bar_cmd.erase()
                self.bar_cmd.addstr(":" + read_string)
                self.bar_cmd.refresh()

            else:
                if c < 256:
                    read_string += chr(c)
                    cursor+=1
                continue

        self.Noecho()
        self.CursorHide()

        self.Release()
        return read_string

    def Display(self, string, x=0, y=0, bold=False, highlight=False,color=False,strike=False):
    #    self.write_string(string,x,y,bold,highlight,color,strike)
    #
    #def write_string(self, string, x=0, y=0, bold=False, highlight=False,color=False,strike=False):
        self.Lock()

        #Does it need to be struck out?
        if(strike):
            string = u'\u0336'.encode("utf-8").join(string) + u'\u0336'.encode("utf-8")

        if(highlight):
            bold = True
            color = C.SCR_COLOR_WHITE_GRAY_BGRD

        options = 0
        if(color):
            options = options | curses.color_pair(color)
        if(bold):
            options = options | curses.A_BOLD

        try:
            self.screen.addstr(x, y, string, options)
        except curses.error:
            #This is probably a cursor error, safe to ignore it?
            #DEBUG.logging.debug("Curses error: Pads throw incorrect size errors")
            pass

        self.Refresh()
        self.Release()


    ########################
    #                      #
    # Screen helpers       #
    #                      #
    ########################
    #Non habiticancurse related helper functions for the screen

    def Lock(self):
        # Synchronize screen input/output
        self.lock.acquire()

    def Release(self):
        # Synchronize screen input/output
        self.lock.release()


    def Refresh(self):
        self.screen.refresh()

    def Erase(self):
        self.screen.erase()

    def Clear(self):
        self.screen.clear()

    def SaveInRegister(self, register):
        # Should be between 0 and C.NUM_CONTEXT_REGISTERS-1
        if register >= C.NUM_CONTEXT_REGISTERS:
            return

        self.ctxts[register].seek(0)
        self.screen.putwin(self.ctxts[register])
        self.active_registers[register] = True

    def RestoreRegister(self, register):
        # Should be between 0 and C.NUM_CONTEXT_REGISTERS-1
        if register >= C.NUM_CONTEXT_REGISTERS:
            return

        # Register is empty
        if not self.active_registers[register]:
            return

        self.ctxts[register].seek(0)
        self.screen = curses.getwin(self.ctxts[register])

        # Clear Notification Line
        self.status_display.erase()
        self.status_display.refresh()

    def Save(self):
        self.stack.append(self.stackFile.tell())
        self.screen.putwin(self.stackFile)

    def Restore(self):
        # Stack cannot be empty
        if len(self.stack) == 0:
            return

        self.stackFile.seek(self.stack[-1])
        self.screen = curses.getwin(self.stackFile)

        # Clear Notification Line
        self.status_display.erase()
        self.status_display.refresh()

        self.Refresh()

    def Highlight(self, string, x=0, y=0):
        self.Display(string, x, y, highlight=True)

    def GetCharacter(self):
        self.Lock()
        c = self.screen.getch()
        self.Release()
        return c

    def Echo(self):
        curses.echo()

    def Noecho(Self):
        curses.noecho()

    def CursorBlink(self):
        curses.curs_set(1)

    def CursorHide(self):
        curses.curs_set(0)

    def ClearRegion(self, x1, x2, y1, y2):
        for i in xrange(x1, x2):
            self.Display(" "*(y2 - y1), i, y1)

    def ClearTextArea(self):
        # Clear the area where tasks are displayed
        self.ClearRegion(C.SCR_MAX_MENU_ROWS+7, C.SCR_X-2, 0, C.SCR_Y)


    def StringInput(self, x=0, y=0):
        self.Lock()
        self.Echo()
        self.CursorBlink()

        inpString = self.screen.getstr(x, y, C.SCR_Y-20)

        self.Noecho()
        self.CursorHide()
        self.Release()

        return inpString

    def ScrollBar(self, X, Y, start, end, length, rows = -1):
        self.Lock()
        if length == 0:       # Empty Menu
            return
        if rows == -1:
            rows = C.SCR_MAX_MENU_ROWS

        start_space = int(math.ceil((start * 1.0)/(length) * rows))
        end_space   = int(math.floor(((length - end) * 1.0)/(length) * rows))

        self.Display(C.SYMBOL_UP_TRIANGLE,X-1, Y,
                                    color=C.SCR_COLOR_DARK_GRAY, bold=True)
        self.Display(C.SYMBOL_DOWN_TRIANGLE,X+rows, Y,
                                    color=C.SCR_COLOR_DARK_GRAY, bold=True)

        starting = X
        ending   = X + rows
        for i in xrange(start_space):
            self.Display(" ", X+i, Y, color=C.SCR_COLOR_WHITE_GRAY_BGRD,bold=True)
            starting = X + i

        for i in xrange(end_space):
            self.Display(" ",X+rows-1-i, Y,
                             color=C.SCR_COLOR_WHITE_GRAY_BGRD,bold=True)
            ending = X + rows - 1 - i

        for i in xrange(starting, ending):
            self.Display(" ",i, Y,color=C.SCR_COLOR_GRAY_WHITE_BGRD, bold=True)

        self.Release()
