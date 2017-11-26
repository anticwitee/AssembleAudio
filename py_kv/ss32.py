from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.write()

from kivy.app import App
from kivy.core.window import Window
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
from kivy.uix.behaviors.compoundselection import CompoundSelectionBehavior
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.settings import SettingsWithSidebar
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
import parse_kivy


#widget.walk(restrict=True)



from kivy.config import ConfigParser
config = ConfigParser()
config.read('ss32.ini')

def set_up(cfg_ins, filename):
    global cfg_recur_depth
    cfg_recur_depth = cfg_ins.getdefaultint('internals', 'recursion_depth', 1)

    global cfg_primary_deep
    raw_primary_deep = cfg_ins.getdefault('colours', 'primary_deep', '0c3c60')
    cfg_primary_deep = get_color_from_hex(raw_primary_deep)

    global cfg_primary_medium
    raw_primary_medium = cfg_ins.getdefault('colours', 'primary_medium', '39729b')
    cfg_primary_medium = get_color_from_hex(raw_primary_medium)

    global cfg_primary_light
    raw_primary_light = cfg_ins.getdefault('colours', 'primary_light', '6ea4ca')
    cfg_primary_light = get_color_from_hex(raw_primary_light)

    global cfg_primary_neutral
    raw_primary_neutral = cfg_ins.getdefault('colours', 'primary_neutral', 'dbdbdb')
    cfg_primary_neutral = get_color_from_hex(raw_primary_neutral)

    global cfg_primary_dark
    raw_primary_dark = cfg_ins.getdefault('colours', 'primary_dark', '21252B')
    cfg_primary_dark = get_color_from_hex(raw_primary_dark)

    global cfg_aux_dark
    raw_aux_dark = cfg_ins.getdefault('colours', 'aux_dark', '3e3a47')
    cfg_aux_dark = get_color_from_hex(raw_aux_dark)

    global cfg_aux_neutral
    raw_aux_neutral = cfg_ins.getdefault('colours', 'aux_neutral', 'd1e0eb')
    cfg_aux_neutral = get_color_from_hex(raw_aux_neutral)

    global cfg_aux_deep
    raw_aux_deep = cfg_ins.getdefault('colours', 'aux_deep', '39273F')
    cfg_aux_deep = get_color_from_hex(raw_aux_deep)

    global cfg_select_medium
    raw_select_medium = cfg_ins.getdefault('colours', 'select_medium', '553A5E')
    cfg_select_medium = get_color_from_hex(raw_select_medium)


    try:
         with open(filename, 'r+') as kv_file:
             for i in range(7):
                 next(kv_file)

             colour_list = [raw_primary_deep, raw_primary_medium, raw_primary_light,
                raw_primary_neutral, raw_aux_neutral, raw_primary_dark, raw_aux_dark, raw_aux_deep]

             for i in range(8):
                line = kv_file.readline().strip()
                if line[:2] == '#:':
                    start, hex_code, end = line.split("'")
                    hex_code = colour_list[i]
                    new_line = "'".join([start, hex_code, end])
                    #print(new_line)

                else:
                    print("Comment, this shouldn't occur.")
    except IOError:
        print("--- modify_kv: Problem opening file.")



set_up(config, 'ss32.kv')


class GridOfButtons(FocusBehavior, CompoundSelectionBehavior):

    def __init__(self):
        self._avail = 0
        self._sel_file = ""
        self._sel_start = None
        self._sel_end = None



    def button_press(self, button, touch):
        if button.collide_point(touch.x, touch.y):
            self.grid_touch_actions(button, touch)


    def create_grid(self, x_hint_list, rows_to_create):
        #x_hint_list is a list of ints, relating to the intended
        #width of each column in the grid.

        for row in range(rows_to_create):
            for x_hint in x_hint_list:
                grid_button = Button(text = '', valign = 'middle', shorten = True, size_hint_y = None,
                    height = 30,  size_hint_x = x_hint, background_color = cfg_primary_neutral,
                    background_normal = '', color = cfg_primary_dark)

                grid_button.bind(size=grid_button.setter('text_size'))
                grid_button.bind(on_touch_down=self.button_press)
                self.add_widget(grid_button)
        self._avail += rows_to_create


    def iterate_row(self, start = 0, match = ''):
        for i, widget in enumerate(reversed(self.children[start::self.cols])):
            if widget.text == match:
                return i

    def get_row_index(self, pathname):
        return self.iterate_row(match = pathname)

    def find_next_row(self):
        return self.iterate_row()

    def clear_grid(self):
        for widget in self.children:
            widget.text = ''
        self._avail = len(self.children) // self.cols


    def get_last_row_range_simple(self):
        #Assumes 0-1 rows have been removed
        total_rows = len(self.children) // self.cols
        last_row_index = total_rows - self._avail
        end = len(self.children) - (last_row_index * self.cols)
        start = end - self.cols
        return (start, end)


    def get_last_row_range_full(self):
        #Index starts from the bottom right in this method.
        last_row_index = None
        for i, widget in enumerate(self.children[::self.cols]):
            if widget.text != '':
                last_row_index = i
                break

        if last_row_index != None:
            start = last_row_index * self.cols
            end = start + self.cols
            return (start, end, last_row_index)
        return (False, False, False)


    def remove_row(self, start, end, swap = False):
        data_to_write = []
        for widget in reversed(self.children[start:end]):
            data_to_write.append(widget.text)
            widget.text = ''
        if not swap:
            self._avail += 1
        return data_to_write


    def auto_reshuffle(self):
        start, end = self.get_last_row_range_simple()
        data_to_write = self.remove_row(start, end, swap = True)
        next_avail = self.find_next_row()
        self.edit_row(next_avail, data_to_write)


    def edit_row(self, index, data_to_write):
        if len(data_to_write) != self.cols:
            print("--Edit Row:  Data mismatch error.")
            popup = Popup(title='Grid Error 01',
                    content=Label(text = 'There was a problem in updating the grid.'),
                    size_hint = (0.3, 0.3))
            popup.open()
        else:
            end = len(self.children) - (index * self.cols)
            start = end - self.cols
            for i, widget in enumerate(reversed(self.children[start:end])):
                widget.text = data_to_write[i]


    def set_info(self, data_to_write, x_hint_list, num_rows_to_add = 3):
        #Takes in the file data, and updates the Grid to represent
        #and indicate the files that are loaded with their metadata.

        if len(data_to_write) != self.cols:
            print("--Set info:  Data mismatch error.")
            popup = Popup(title='Grid Error 02',
                    content=Label(text = 'There was a problem in updating the grid.'),
                    size_hint = (0.3, 0.3))
            popup.open()
        else:
            threshold = 3
            #If < threshold available rows left, add more
            if self._avail < threshold:
                self.create_grid(x_hint_list, num_rows_to_add)

            length = len(self.children)
            next_row = self.find_next_row()
            end = length - (next_row * self.cols)
            start = end - self.cols
            for i, widget in enumerate(reversed(self.children[start:end])):
                #strip text primarily for title and artist, so shorten
                #doesn't take into account the trailing whitespace
                widget.text = data_to_write[i].strip()
            self._avail -= 1

    def grid_touch_actions(self, child, touch):
        if child.collide_point(touch.x, touch.y):
            if touch.is_double_tap and touch.button == 'left':
                self.show_load()
            else:
                #Single-click
                #Deselect visually
                for widget in self.children[self._sel_start: self._sel_end]:
                    widget.background_color = cfg_primary_neutral
                    widget.color = cfg_primary_dark

                index = (len(self.children) - 1) - self.children.index(child)
                row = index // self.cols
                end = len(self.children) - (row * self.cols)
                start = end - self.cols

                self._sel_file = self.children[start].text
                self._sel_start = start
                self._sel_end = end

                #Checks for empty rows
                if self._sel_file:
                    if touch.button == 'left':
                        #Visual selection
                        for widget in self.children[self._sel_start: self._sel_end]:
                            widget.background_color = cfg_select_medium
                            widget.color = cfg_primary_neutral

                    elif touch.button == 'right':
                        self.remove_row(self._sel_start, self._sel_end)
                        #self.auto_reshuffle()


    def __str__(self):
        length = '{} {}'.format('Grid of size:', len(self.children))
        return '{}'.format(length)

class RootScreen(BoxLayout):
    pass

class TopMenu(BoxLayout):
    pass

class Frequent(BoxLayout):
    pass

class NetworkQueueHeader(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        x_hint_list = [0.45, 0.55]
        cols = len(x_hint_list)
        col_names = ['Filename', 'Pathname']

        for col in range(cols):
            label = Label(text = col_names[col], size_hint_y = None, height = 30,
                        size_hint_x = x_hint_list[col], bold = True)
            self.add_widget(label)

class NetworkQueueScroll(ScrollView):
    pass


class NetworkQueue(GridLayout, GridOfButtons):

    x_hint_list = [0.45, 0.55]

    def __init__(self, **kwargs):
        super(NetworkQueue, self).__init__(**kwargs)
        self.create_grid(NetworkQueue.x_hint_list, 35)


    def set_info(self, data_to_write):
        GridOfButtons.set_info(self, data_to_write, NetworkQueue.x_hint_list)

    #FileChooserMethods
    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.75, 0.75))
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

    def __str__(self):
        source = '{} {}'.format('Source:', 'Network Queue')
        return '{}\n{}'.format(source, super().__str__())

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        x_hint_list = [0.05, 0.15, 0.15, 0.075, 0.20, 0.075, 0.3]
        cols = len(x_hint_list)
        col_names = ['ID', 'Title', 'Artist', 'End Date',
                    'Filename', 'Type', 'Pathname']

        for col in range(cols):
            label = Label(text = col_names[col], size_hint_y = None, height = 30,
                        size_hint_x = x_hint_list[col], bold = True)
            self.add_widget(label)

class EditingGridScroll(ScrollView):
    pass


class EditingGrid(GridLayout, GridOfButtons):

    _sel_file = StringProperty('')
    x_hint_list = [0.05, 0.15, 0.15, 0.075, 0.20, 0.075, 0.3]

    def __init__(self, **kwargs):
        super(EditingGrid, self).__init__(**kwargs)
        self.create_grid(EditingGrid.x_hint_list, 30)
        Window.bind(on_dropfile=self.file_drop)


    def file_drop(self, window, path_in_bytes):
        from os.path import isdir
        a_path = path_in_bytes.decode('utf-8')
        list_of_files = [a_path]
        if isdir(a_path):
            list_of_files = self.files_from_directory(a_path)
        self.load("Dropped files", list_of_files)

    def files_from_directory(self, directory, depth = cfg_recur_depth):
        from os import listdir
        from os.path import isfile, join

        file_list = []
        for a_path in listdir(directory):
            a_path = join(directory, a_path)
            if isfile(a_path):
                file_list.append(a_path)
            elif depth > 1:
                file_list.extend(self.files_from_directory(a_path, depth = depth - 1))
        return file_list


    def set_info(self, data_to_write):
        GridOfButtons.set_info(self, data_to_write, EditingGrid.x_hint_list)

    #FileChooserMethods
    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.75, 0.75))
        self._popup.open()

    def info_from_file(self, filename):
        from os.path import basename, splitext
        try:
            with open(filename, 'rb') as f:
                f.seek(72)
                try:
                    title = f.read(43).decode("utf-8")
                except UnicodeDecodeError:
                    title = "None"

                try:
                    id_num = f.read(4).decode("utf-8")
                except UnicodeDecodeError:
                    id_num = "None"

                f.seek(139)
                try:
                    end_date = f.read(6).decode("utf-8")
                except UnicodeDecodeError:
                    end_date = "None"

                f.seek(335)
                try:
                    artist = f.read(34).decode("utf-8")
                except UnicodeDecodeError:
                    artist = "None"
            data_to_write = [id_num, title, artist, end_date, basename(filename), splitext(filename)[1], filename]
            return data_to_write

        except IOError:
            print("--info_from_file-- Cannot find file {}".format(filename))
            popup = Popup(title='File Error',
                    content=Label(text = 'Cannot find file {}'.format(filename)),
                    size_hint = (0.3, 0.3))
            popup.open()

    def load(self, path, filenames):
        #Should check file type first.
        print("Path: ", path)
        print("Filenames: ", filenames)

        for filename in filenames:
            data = self.info_from_file(filename)
            if data:
                self.set_info(data)
        if path != "Dropped files":
            self.dismiss_popup()


    def dismiss_popup(self):
        self._popup.dismiss()


    def __str__(self):
        source = '{} {}'.format('Source:', 'Editing Grid')
        return '{}\n{}'.format(source, super().__str__())


class EditingGridCommands(BoxLayout):
    editing_grid = ObjectProperty(None)

    def clear_grid(self):
        GridOfButtons.clear_grid(self.editing_grid)

    def reshuffle(self):
        #Index from row_range_full is from bottom right
        while True:
            start, end, last_row_index = self.editing_grid.get_last_row_range_full()
            if not start:
                #Grid is empty
                break
            elif last_row_index == self.editing_grid._avail:
                #Grid has no empty spaces
                break
            else:
                data_to_write = self.editing_grid.remove_row(start, end, swap = True)
                index = self.editing_grid.find_next_row()
                self.editing_grid.edit_row(index, data_to_write)


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)



class UserInput(BoxLayout):
    path_name = StringProperty('')
    editing_grid = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(UserInput, self).__init__(**kwargs)
        self._sound = None
        self._sound_pos = None
        self._update_bar_schedule = None

    def update_volume(self, volume):
        if self._sound:
            self._sound.volume = volume

    def update_bar(self, dt):
        if self._sound:
            if self._sound.state == 'play':
                self.ids.p_bar.value = self._sound.get_pos()
            else:
                #Sound has naturally stopped
                if self._sound_pos == None:
                    self.ids.p_bar.value = 0
                self._update_bar_schedule.cancel()


    def pause(self):
        self._sound_pos = self._sound.get_pos()
        self._update_bar_schedule.cancel()
        self._sound.stop()

    def resume(self):
        self._update_bar_schedule()
        self._sound.play()

        if self._sound_pos:
            self._sound.seek(self._sound_pos)
        self._sound_pos = None

    def play(self, path):
        from kivy.core.audio import SoundLoader

        if not self._sound:
            self.load_audio_file(path)
        elif self._sound.source == path:
            if self._sound.state == "play":
                self.pause()
            else:
                self.resume()
        else:
            #they want to play a different file
            self.unload_audio_file()
            self.load_audio_file(path)

    def unload_audio_file(self):
        if self._sound:
            self._update_bar_schedule.cancel()
            self._sound.stop()
            self._sound_pos = None
            self._sound.unload()


    def load_audio_file(self, path):
        from kivy.core.audio import SoundLoader

        sound = SoundLoader.load(path)
        self._sound = sound

        if sound:
            update_bar_schedule = Clock.schedule_interval(self.update_bar, 1)
            self._update_bar_schedule = update_bar_schedule

            self.ids.p_bar.max = sound.length
            sound.volume = self.ids.volume_slider.value
            sound.play()
        else:
            print("Cannot play the file %s." % path)
            error_msg = 'Cannot play the file %s.' % (path) if path else 'No file selected.'
            popup = Popup(title='Audio Error.',
                    content=Label(text= error_msg),
                    size_hint = (0.3, 0.3))
            popup.open()


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

        if filename:
            ret_values = parse_kivy.wav_File_Handler(filename, edit, new_name = rename)
            #Update the EditingGrid to display accurate info
            if ret_values:
                renamed, edited = ret_values
                if renamed or edited:
                    if renamed and edited:
                        data = EditingGrid.info_from_file(self, renamed)
                    else:
                        data = EditingGrid.info_from_file(self, filename)

                    index = GridOfButtons.get_row_index(self.editing_grid, filename)
                    if data and (index != None):
                        GridOfButtons.edit_row(self.editing_grid, index, data)
        else:
            error_msg = 'No file selected.'
            popup = Popup(title='Conversion/Editing Error.',
                    content=Label(text= error_msg),
                    size_hint = (0.3, 0.3))
            popup.open()





class Config(Screen):
    pass

class ss32App(App):
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        return

    def build_config(self, config):
        config.read('ss32.ini')


    def build_settings(self, settings):
        settings.add_json_panel('SS32 Conf', self.config, 'ss32.json')


    def on_config_change(self, config, section, key, value):
        print(config, section, key, value)



if __name__ == '__main__':
    ss32App().run()
