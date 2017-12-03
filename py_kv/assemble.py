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
from kivy.lang.builder import Builder
import modify_wav


from os.path import basename, splitext

#widget.walk(restrict=True)


from kivy.utils import get_color_from_hex
from kivy.config import ConfigParser
config = ConfigParser()
config.read('assembleaudio.ini')

def set_up(cfg_ins):
    global cfg_recur_depth
    cfg_recur_depth = cfg_ins.getdefaultint('internals', 'recursion_depth', 1)

    global cfg_primary_deep
    global raw_primary_deep
    raw_primary_deep = cfg_ins.getdefault('colours', 'primary_deep', '0c3c60')
    cfg_primary_deep = get_color_from_hex(raw_primary_deep)

    global cfg_primary_medium
    global raw_primary_medium
    raw_primary_medium = cfg_ins.getdefault('colours', 'primary_medium', '39729b')
    cfg_primary_medium = get_color_from_hex(raw_primary_medium)

    global cfg_primary_light
    global raw_primary_light
    raw_primary_light = cfg_ins.getdefault('colours', 'primary_light', '6ea4ca')
    cfg_primary_light = get_color_from_hex(raw_primary_light)

    global cfg_primary_neutral
    global raw_primary_neutral
    raw_primary_neutral = cfg_ins.getdefault('colours', 'primary_neutral', 'dbdbdb')
    cfg_primary_neutral = get_color_from_hex(raw_primary_neutral)

    global cfg_primary_dark
    global raw_primary_dark
    raw_primary_dark = cfg_ins.getdefault('colours', 'primary_dark', '21252B')
    cfg_primary_dark = get_color_from_hex(raw_primary_dark)

    global cfg_aux_dark
    global raw_aux_dark
    raw_aux_dark = cfg_ins.getdefault('colours', 'aux_dark', '3e3a47')
    cfg_aux_dark = get_color_from_hex(raw_aux_dark)

    global cfg_aux_neutral
    global raw_aux_neutral
    raw_aux_neutral = cfg_ins.getdefault('colours', 'aux_neutral', 'd1e0eb')
    cfg_aux_neutral = get_color_from_hex(raw_aux_neutral)

    global cfg_aux_deep
    global raw_aux_deep
    raw_aux_deep = cfg_ins.getdefault('colours', 'aux_deep', '39273F')
    cfg_aux_deep = get_color_from_hex(raw_aux_deep)

    global cfg_select_medium
    raw_select_medium = cfg_ins.getdefault('colours', 'select_medium', '553A5E')
    cfg_select_medium = get_color_from_hex(raw_select_medium)



set_up(config)



class GridOfButtons(FocusBehavior, CompoundSelectionBehavior):

    def __init__(self):
        self._avail = 0
        self._sel_file = ''
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
        self._sel_file = ''
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
            print('--Edit Row:  Data mismatch error.')
            popup = Popup(title='Grid Error 01',
                    content=Label(text = 'There was a problem in updating the grid.'),
                    size_hint = (0.3, 0.3))
            popup.open()
        else:
            end = len(self.children) - (index * self.cols)
            start = end - self.cols
            #Update the selected file's info too.
            if self.children[start].text == self._sel_file:
                self._sel_file = data_to_write[-1]
            for i, widget in enumerate(reversed(self.children[start:end])):
                widget.text = data_to_write[i].strip()


    def set_info(self, data_to_write, x_hint_list, num_rows_to_add = 3):
        #Takes in the file data, and updates the Grid to represent
        #and indicate the files that are loaded with their metadata.

        if len(data_to_write) != self.cols:
            print('--Set info:  Data mismatch error.')
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


class GridOfButtonsFChoose(GridOfButtons):

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title='Load file', content=content,
                            size_hint=(0.75, 0.75))
        self._popup.open()

    def load(self, path, filenames):
        print(path, filenames)
        for filename in filenames:
            data_to_write = [basename(filename), filename]
            self.set_info(data_to_write)

        if path != 'auto-add':
            self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()


class RootScreen(BoxLayout):
    pass


class TopMenu(BoxLayout):
    pass


class Frequent(BoxLayout):
    pass





class CategoriesHeader(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        x_hint_list = [0.35, 0.55]
        cols = len(x_hint_list)
        col_names = ['Name', 'Description']

        for col in range(cols):
            label = Label(text = col_names[col], size_hint_y = None, height = 30,
                        size_hint_x = x_hint_list[col], bold = True)
            self.add_widget(label)


class CategoriesScroll(ScrollView):
    pass


class CategoriesList(GridLayout, GridOfButtonsFChoose):

    x_hint_list = [0.35, 0.65]

    def __init__(self, **kwargs):
        super(CategoriesList, self).__init__(**kwargs)
        self.create_grid(CategoriesList.x_hint_list, 35)

    def set_info(self, data_to_write):
        GridOfButtons.set_info(self, data_to_write, CategoriesList.x_hint_list)


    #def load(self):

    #def grid_touch_actions(self): (or modify GridOfButtons)
    


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


class NetworkQueue(GridLayout, GridOfButtonsFChoose):

    x_hint_list = [0.45, 0.55]

    def __init__(self, **kwargs):
        super(NetworkQueue, self).__init__(**kwargs)
        self.create_grid(NetworkQueue.x_hint_list, 35)

    def set_info(self, data_to_write):
        GridOfButtons.set_info(self, data_to_write, NetworkQueue.x_hint_list)


    def load(self, path, filenames):
        print(path, filenames)
        for filename in filenames:
            data_to_write = [basename(filename), filename]
            self.set_info(data_to_write)

        if path != 'auto-add':
            self.dismiss_popup()


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
        pass

    def display_log(self):
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


class EditingGrid(GridLayout, GridOfButtonsFChoose):

    network_queue = ObjectProperty(None)
    user_input = ObjectProperty(None)
    _sel_file = StringProperty('')

    x_hint_list = [0.05, 0.15, 0.15, 0.075, 0.20, 0.075, 0.3]
    info_items = ['audio_id', 'title', 'artist', 'e_date']

    def __init__(self, **kwargs):
        super(EditingGrid, self).__init__(**kwargs)
        self.create_grid(EditingGrid.x_hint_list, 30)
        Window.bind(on_dropfile=self.file_drop)


    def grid_touch_actions(self, child, touch):
        super().grid_touch_actions(child, touch)
        self.user_input.fill_text_inputs(self._sel_file)


    def file_drop(self, window, path_in_bytes):
        from os.path import isdir
        a_path = path_in_bytes.decode('utf-8')
        list_of_files = [a_path]
        if isdir(a_path):
            list_of_files = self.files_from_directory(a_path)
        self.load('Dropped files', list_of_files)


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



    def load(self, path, filenames):
        print('Path: ', path)
        print('Filenames: ', filenames)

        for filename in filenames:
            data = modify_wav.info_from_file(filename, EditingGrid.info_items)
            if data:
                data.extend([basename(filename), splitext(filename)[1], filename])
                self.set_info(data)
        if path != 'Dropped files':
            self.dismiss_popup()


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



class FileManipulation(BoxLayout):
    pass

class UserInput(BoxLayout):

    editing_grid = ObjectProperty(None)
    network_queue = ObjectProperty(None)
    info_items = [
        'e_hour', 'e_date', 's_hour', 's_date', 'eom', 'intro',
        'end', 'year', 'audio_id', 'artist', 'title', 'note'
        ]

    def fill_text_inputs(self, filename):
        if filename:
            #Update the TextInputs to represent current-data.
            data = ['99:99:99']
            data.extend(modify_wav.info_from_file(filename, self.info_items))
            data.append(basename(filename))
            data.insert(3, '00:00:00')
        else:
            data = ['' for i in range(15)]
        counter = 0
        for box_layout in self.children:
            for text_input in box_layout.children:
                text_input.text = str(data[counter]).strip()
                counter += 1


    # def overwrite_popup(self, path):
    #     box = BoxLayout(orientation='vertical')
    #     lab = Label(
    #         text='File {} already exists. Do you want to overwrite it?'.format(path),
    #         size_hint_y=0.7
    #         )
    #     button1 = Button(text='Yes')
    #     button2 = Button(text='No')
    #     box_inside = BoxLayout(size_hint_y=0.3)
    #     box_inside.add_widget(button1)
    #     box_inside.add_widget(button2)
    #     box.add_widget(lab)
    #     box.add_widget(box_inside)
    #     content = box
    #
    #     popup = Popup(title='File already exists.',
    #                 content=content,
    #                 size_hint=(0.4, 0.4))
    #
    #     button1.bind(on_press=lambda x: self.overwrite_ans(popup, 'yes'))
    #     button2.bind(on_press=lambda x: self.overwrite_ans(popup, 'no'))
    #     popup.open()
    #
    # def overwrite_ans(self, popup, value):
    #     popup.dismiss()
    #     return value



    def modify_file(self, filename, user_data, rename=''):
        #Sanitise the input. Then call a handler to deal with
        #the specific file. Then update the grid to reflect changes.
        if filename:
            edit = self.probe_text_inputs(user_data)
            final_filename = filename
            if rename != basename(filename):
                result = modify_wav.renameScott(filename, rename)
                if result == 'owrite':
                    print('owrite')
                    #popup to ask user if they want to overwrite
                else:
                    final_filename = result

            modify_wav.wavFileHandler(final_filename, edit)
            #Update the EditingGrid to display accurate info
            index = GridOfButtons.get_row_index(self.editing_grid, filename)
            data = modify_wav.info_from_file(final_filename, EditingGrid.info_items)
            if data and index is not None:
                data.extend([basename(final_filename), splitext(final_filename)[1], final_filename])
                GridOfButtons.edit_row(self.editing_grid, index, data)

            #Update the network queue
            self.network_queue.load('auto-add', [final_filename])
        else:
            error_msg = 'No file selected.'
            popup = Popup(title='Conversion/Editing Error.',
                    content=Label(text= error_msg),
                    size_hint = (0.3, 0.3))
            popup.open()


    def process_text_inputs(self):
        user_data_raw = []
        for box_layout in self.children:
            for text_input in box_layout.children:
                user_data_raw.append(text_input.text)

        new_name = user_data_raw.pop()
        user_data = []
        for i in range(len(user_data_raw)):
            header = user_data_raw.pop()
            #Temporary
            if i != 10 and i != 13:
                user_data.append(header)
        self.modify_file(self.editing_grid._sel_file, user_data, rename=new_name)


    def probe_text_inputs(self, user_data):
        #Takes the list of info from the user. If they are the correct
        #length, then they will be converted to the appropriate data type
        #and added to an 'edit' list.

        #should add namedTuples
        # (name, data_type, length)
        field_info = [
            ('note', 'str', 34), ('title', 'str', 43), ('artist', 'str', 34),
            ('audio_id', 'str', 4), ('year', 'str', 4), ('end', 'str', 1),
            ('intro', 'str', 2), ('eom', 'int', 6), ('s_date', 'str', 6),
            ('s_hour', 'int', 1), ('e_date', 'str', 6), ('e_hour', 'int', 1)
        ]


        edit = []
        for i, attrib in enumerate(user_data):
            if len(attrib) == field_info[i][2]:
                if field_info[i][1] == 'int' and isinstance(attrib, int):
                    attrib = int(attrib)
                elif not field_info[i][1] == 'str':
                    print('---probe_text_inputs Arg {} should be an int. Data: {}.---'.format(i, attrib))
            elif i < 3 and attrib:
                attrib += ' ' * (field_info[i][2] - len(attrib))
            elif attrib:
                print('---probe_text_inputs---')
                print('{} is the incorrect length. Data: {}---'.format(field_info[i][0], attrib))
                print(len(attrib), field_info[i][2], attrib)
                print(user_data)
                continue
            name = field_info[i][0]
            edit.append((name, attrib))
        return edit



class PlayBack(GridLayout):

    path_name = StringProperty('')
    user_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PlayBack, self).__init__(**kwargs)
        self._sound = None
        self._sound_pos = None
        self._update_bar_schedule = None


    def notify_usr_input(self):
        self.user_input.process_text_inputs()


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
            if self._sound.state == 'play':
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
            print('Cannot play the file %s.' % path)
            error_msg = 'Cannot play the file %s.' % (path) if path else 'No file selected.'
            popup = Popup(title='Audio Error.',
                    content=Label(text= error_msg),
                    size_hint = (0.3, 0.3))
            popup.open()



class Misc(BoxLayout):
    pass

class StatsGrid(GridLayout):
    sel_file_stats = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_stats()

    def create_stats(self):
        num_labels = 70 * 2
        for i in range(num_labels):
            label = Label(shorten=True)
            label.bind(size=label.setter('text_size'))
            self.add_widget(label)
        self.get_stats()

    def get_stats(self):
        headers = [('RIFF', 'No File Selected'), ('File length - 8', 'No File Selected'),
            ('WAVE', 'No File Selected'), ('fmt', 'No File Selected'), ('FMT Chunk size', 'No File Selected'),
            ('Format Category', 'No File Selected'), ('Number of channels', 'No File Selected'),
            ('Sampling Rate', 'No File Selected'), ('Avg bytes/sec', 'No File Selected'),
            ('Data block size', 'No File Selected'), ('Format', 'No File Selected'),
            ('White space', 'No File Selected'), ('scot', 'No File Selected'),
            ('424 Constant', 'No File Selected'), ('Alter(scratchpad)', 'No File Selected'),
            ('Attrib(scratchpad)', 'No File Selected'), ('Artnum(scratchpad)', 'No File Selected'),
            ('Title', 'No File Selected'), ('ID', 'No File Selected'), ('Padding', 'No File Selected'),
            ('Approx duration', 'No File Selected'), ('Cue-in (secs)', 'No File Selected'),
            ('Cue-in (hundredths)', 'No File Selected'), ('Total Length (seconds)', 'No File Selected'),
            ('Total Length (hundredths)', 'No File Selected'), ('Start Date', 'No File Selected'),
            ('End date', 'No File Selected'), ('Start hour', 'No File Selected'),
            ('End hour', 'No File Selected'), ('Digital', 'No File Selected'),
            ('Sample Rate', 'No File Selected'), ('Mono/Stereo', 'No File Selected'),
            ('Compress', 'No File Selected'), ('Eomstrt', 'No File Selected'),
            ('EOM (Hundredths from end)', 'No File Selected'), ('Attrib2', 'No File Selected'),
            ('Future', 'No File Selected'), ('catfontcolor', 'No File Selected'),
            ('catcolor', 'No File Selected'), ('segeompos', 'No File Selected'),
            ('vtstartsecs', 'No File Selected'), ('vtstarthunds', 'No File Selected'),
            ('priorcat', 'No File Selected'), ('priorcopy', 'No File Selected'),
            ('priorpadd', 'No File Selected'), ('postcat', 'No File Selected'),
            ('postcopy', 'No File Selected'), ('postpadd', 'No File Selected'),
            ('hrcanplay', 'No File Selected'), ('future', 'No File Selected'),
            ('Artist', 'No File Selected'), ('Note', 'No File Selected'),
            ('Intro', 'No File Selected'), ('End', 'No File Selected'),
            ('Year', 'No File Selected'), ('Obsolete2', 'No File Selected'),
            ('Hour Recorded', 'No File Selected'), ('Date Recorded', 'No File Selected'),
            ('Mpegbitrate', 'No File Selected'), ('Pitch', 'No File Selected'),
            ('playlevel', 'No File Selected'), ('lenvalid', 'No File Selected'),
            ('filelength', 'No File Selected'), ('desiredlen', 'No File Selected'),
            ('triggers[4]', 'No File Selected'), ('fillout', 'No File Selected'),
            ('fact', 'No File Selected'), ('4????', 'No File Selected'),
            ('Number of Audio Samples', 'No File Selected'), ('Data', 'No File Selected'),
            ('file length - 512', 'No File Selected')]

        if self.sel_file_stats:
            headers = modify_wav.getWavInfo(self.sel_file_stats)
        for i, label in enumerate(reversed(self.children)):
            label.text = str(headers[i // 2][ i % 2 ])

class AssembleAudioApp(App):

    def get_primary_deep(self):
        return raw_primary_deep

    def get_primary_medium(self):
        return raw_primary_medium

    def get_primary_light(self):
        return raw_primary_light

    def get_primary_neutral(self):
        return raw_primary_neutral

    def get_primary_dark(self):
        return raw_primary_dark

    def get_aux_dark(self):
        return raw_aux_dark

    def get_aux_neutral(self):
        return raw_aux_neutral

    def get_aux_deep(self):
        return raw_aux_deep


    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        return Builder.load_file('assemble.kv')

    def build_config(self, config):
        config.read('assembleaudio.ini')

    def build_settings(self, settings):
        settings.add_json_panel('AssembleAudio Configuration', self.config, 'conf.json')


    def on_config_change(self, config, section, key, value):
        print(config, section, key, value)



if __name__ == '__main__':
    AssembleAudioApp().run()
