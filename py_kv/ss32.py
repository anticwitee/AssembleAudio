from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
import parse_kivy


#Improve selection/availability mechanic
#Drop file
#NetworkCommands needs to be set up properly

class GridOfButtons():
    # #set initial widths
    # print(len(self.children))
    # for i, widget in enumerate(self.children[:len(self.children) - self.cols]):
    #     print(i, widget)
    #     widget.width = pre_defined_widths[i % 7]

    def create_grid(self, width_list, rows_to_create):
        #Width_list is a list of ints, relating to the intended
        #width of each column in the grid.

        for row in range(rows_to_create):
            for width_of_col in width_list:
                grid_button = Button(text = '', valign = 'middle', size_hint_y = None,
                    height = 50, width = width_of_col, background_color = (1,0,0,1))
                grid_button.bind(size=grid_button.setter('text_size'))
                self.add_widget(grid_button)

    def set_info(self, data_to_write, width_list, num_rows_to_add = 3):
        #Takes in the file data, and updates the Grid to represent
        #and indicate the files that are loaded with their metadata.

        if len(data_to_write) != self.cols:
            print("--set_info Data mismatch error.")
        else:
            threshold = 3
            rows = len(self.children) // self.cols
            #If < threshold available rows left, add more
            if (self._avail + threshold) >= rows:
                self.create_grid(width_list, num_rows_to_add)

            length = len(self.children)
            end = length - (self._avail * self.cols)
            start = end - self.cols
            for i, widget in enumerate(reversed(self.children[start:end])):
                widget.text = data_to_write[i]
            self._avail += 1


    def on_touch_up(self, touch, out_of_bounds = ""):
        if not self.collide_point(touch.x, touch.y):
            print("--- %s Should use the super function." % out_of_bounds)

        elif touch.is_double_tap and touch.button == 'left':
            print("Available slot: ", self._avail)
            self.show_load()

        else:
            #Single-click
            for row, widget in enumerate(reversed(self.children[::self.cols])):
                if touch.y >= widget.y:
                    #Deselect (could optimise)
                    for widget in self.children[self._sel_start: self._sel_end]:
                        widget.background_color = (1, 1, 1, 1)

                    end = len(self.children) - (row * self.cols)
                    start = end - self.cols

                    self._sel_file = self.children[start].text
                    self._sel_type = self.children[start + 1].text
                    self._sel_row = row
                    self._sel_start = start
                    self._sel_end = end

                    #visual selection
                    if self._sel_file:
                        for widget in self.children[self._sel_start: self._sel_end]:
                            widget.background_color = (0.0, 1.0, 1.0, 1.0)

                    print("Selected Row: ", self._sel_row)
                    print("Start", start, "End", end - 1)
                    print("File Type:", self._sel_type)
                    print("Filename:", self._sel_file)
                    if touch.button == 'left':
                        return
                    elif touch.button == 'right':
                        #implement right click for something
                        if self._sel_file:
                            for widget in self.children[self._sel_start: self._sel_end]:
                                widget.text = ''
                        return


class RootScreen(BoxLayout):
    pass

class TopMenu(BoxLayout):
    pass


class Frequent(BoxLayout):
    pass


class NetworkQueueHeader(BoxLayout):
    pass

class NetworkQueue(GridLayout, GridOfButtons):

    def __init__(self, **kwargs):
        super(NetworkQueue, self).__init__(**kwargs)
        self._avail = 0
        self._sel_row = None
        self._sel_file = ""
        self._sel_type = None
        self._sel_start = None
        self._sel_end = None

        self.create_grid([100, 100], 10)

    def set_info(self, data_to_write):
        GridOfButtons.set_info(self, data_to_write, [100, 100])

    def on_touch_up(self, touch):
        GridOfButtons.on_touch_up(self, touch, out_of_bounds = "NetworkQueue---")


    #FileChooserMethods
    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filenames):
        from os.path import basename

        print(path, filenames)
        for filename in filenames:
            data_to_write = [basename(filename), filename]
            self.set_info(data_to_write)

        self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()


class NetworkCommands(BoxLayout):

        def fetch_files(self):
            pathnames = []
            #needs changing
            for i, widget in enumerate(self.children[::2]):
                if widget.text:
                    pathnames.append(widget.text)
            self.send_files(pathnames)

        def send_files(self, pathnames):
            #Should the validation be elsewhere....
            from ftplib import FTP
            from os.path import basename


            for pathname in pathnames:
                #replace with "if file exists"
                if pathname:
                    ip = ""
                    #Need to implement a way to set IP
                    if ip:
                        ftp = FTP(ip)
                        ftp.login()
                        print("PWD:", ftp.pwd())
                        print(ftp.getwelcome())

                        #store files
                        for pathname in pathnames:
                            filename = basename(pathname)
                            try:
                                ftp.storbinary('STOR ' + filename, open(filename, 'rb'))
                            except IOError:
                                print('---send_files cannot send open {}.---'.format(pathname))

        def display_log(self):
            #this is getting triggered multiple times for some reason
            popup = Popup(title='Network Log',
                    content=Label(text = 'Log is not implemented yet.'),
                    size_hint = (0.3, 0.3))
            popup.open()


class EditingGridHeader(BoxLayout):
    pass


class EditingGrid(GridLayout, GridOfButtons):

    _sel_file = StringProperty('')

    def __init__(self, **kwargs):
        super(EditingGrid, self).__init__(**kwargs)
        self._avail = 0
        self._sel_row = None
        self._sel_file = ""
        self._sel_type = None
        self._sel_start = None
        self._sel_end = None

        self.create_grid([100, 100, 100, 100, 100, 100, 100], 10)
        #self.bind(minimum_height=self.setter('height'))


    def set_info(self, data_to_write):
        GridOfButtons.set_info(self, data_to_write, [100, 100, 100, 100, 100, 100, 100])


    def on_touch_up(self, touch):
        GridOfButtons.on_touch_up(self, touch, out_of_bounds = "EditingGrid---")


    #FileChooserMethods
    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filenames):
        from os.path import basename, splitext

        print("Path: ", path)
        print("Filenames: ", filenames)
        for filename in filenames:
            #Should check file type first.
            try:
                with open(filename, 'rb') as f:
                    f.seek(72)
                    try:
                        title = f.read(43).decode("ascii")
                    except UnicodeDecodeError:
                        title = "None"

                    try:
                        id_num = f.read(4).decode("ascii")
                    except UnicodeDecodeError:
                        id_num = "None"

                    f.seek(139)
                    try:
                        end_date = f.read(6).decode("ascii")
                    except UnicodeDecodeError:
                        end_date = "None"

                    f.seek(335)
                    try:
                        artist = f.read(34).decode("ascii")
                    except UnicodeDecodeError:
                        artist = "None"

                data_to_write = [id_num, title, artist, end_date, basename(filename), splitext(filename)[1], filename]
                self.set_info(data_to_write)


            except IOError:
                print("Cannot find file {}".format(filename))
            self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()



class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)



class UserInput(BoxLayout):
    path_name = StringProperty('')

    def __init__(self, **kwargs):
        super(UserInput, self).__init__(**kwargs)
        self._sound = None
        self._sound_pos = None
        self._sound_clock = None
        self._sound_clock_clean = None

    def update_volume(self, volume):
        if self._sound:
            self._sound.volume = volume

    def update_bar(self, dt):
        if self._sound:
            self.ids.p_bar.value = self._sound.get_pos()

    def clean_up(self, dt):
        print("Cleaned up")
        self._sound_clock.cancel()

    def pause(self):
        self._sound_pos = self._sound.get_pos()
        self._sound_clock.cancel()
        self._sound_clock_clean.cancel()
        self._sound.stop()
        print("Postion:", self._sound_pos)

    def resume(self):
        self._sound_clock()
        cleanup = Clock.schedule_once(self.clean_up, (self._sound.length - self._sound.get_pos()) + 1)
        self._sound_clock_clean = cleanup
        self._sound.play()

        if self._sound_pos:
            print("Seek to:", self._sound_pos)
            self._sound.seek(self._sound_pos)

    def play(self, path):
        from kivy.core.audio import SoundLoader

        #Could be more elegant with regard to
        #natural stopping/self._sound_clock_clean
        if self._sound and self._sound.source == path:
            if self._sound.state == "play":
                self.pause()
            else:
                self.resume()
        else:
            if self._sound:
                self._sound_clock.cancel()
                self._sound_clock_clean.cancel()
                self._sound.stop()
                self._sound_pos = None
                self._sound.unload()

            sound = SoundLoader.load(path)
            self._sound = sound
            print('Path: ', path)
            if sound:
                print("Sound found at", sound.source)
                print("Sound is %3.f seconds" % sound.length)
                progress = Clock.schedule_interval(self.update_bar, 1)
                cleanup = Clock.schedule_once(self.clean_up, sound.length + 1)
                self._sound_clock_clean = cleanup
                self._sound_clock = progress

                self.ids.p_bar.max = sound.length
                sound.volume = self.ids.volume_slider.value
                sound.play()
            else:
                popup = Popup(title='Audio Error.',
                        content=Label(text='Cannot play the file %s.' % path),
                        size_hint = (0.3, 0.3))
                popup.open()
                print("Cannot play the file %s." % path)

    def edit_scot(self, filename, *args, rename = ''):
        #Takes in a variable amount of attributes. If they are the correct
        #length, then they will be converted to the appropriate data type
        #and added to an "edit" list. The edit list is then passed onto a
        #function that writes the actual bytes to the file.

        valid_len = (43, 4, 34, 1, 34, 2, 6, 6, 6, 1, 1)
        dtype = [("title", "str"), ("year", "str"), ("artist" ,"str"),
                 ("end", "str"), ("note", "str"), ("intro", "str"),
                 ("eom", "int"), ("s_date", "str"), ("e_date", "str"),
                 ("s_hour", "str"), ("e_hour", "str")]
        edit = []
        print(args)

        for i in range(len(args)):
            if len(args[i]) == valid_len[i]:
                data = args[i]
                try:
                    if dtype[i][1] == "int":
                        data = int(data)
                except:
                    print("---edit_scot Arg {} should be an int. Data: {}.---".format(i, data))
                else:
                    name = dtype[i][0]
                    edit.append((name, data))
            elif (i == 0 or i == 2 or i == 4) and args[i]:
                data = args[i] + (" " * (valid_len[i] - len(args[i])))
                name = dtype[i][0]
                edit.append((name, data))
            elif args[i]:
                print("---edit_scot Arg {} is a rogue, data: {}---".format(i, args[i]))

        print("---edit_scot Edit List: ", edit)
        print("---edit_scot Rename, ", rename)
        print("---edit_scot Filename, ", filename)
        parse_kivy.EditScott(filename, edit, new_name = rename)



class AScreen(Screen):
    #testable screen
    pass


class Config(Screen):
    pass




class ss32App(App):
    def build(self):
        return

if __name__ == '__main__':
    ss32App().run()
