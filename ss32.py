from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
import parse_kivy



class RootScreen(BoxLayout):

    def gib_args(self, *args):
        #filename, title, year, artist, ending, note, intro, EOM,
        #s_date, e_date, s_hour, e_hour, b_audio, e_audio
        print(args)

class TopMenu(BoxLayout):
    pass


class Frequent(BoxLayout):
    pass


class FileGrid(GridLayout):

    _sel_file = StringProperty('')

    def __init__(self, **kwargs):
        super(FileGrid, self).__init__(**kwargs)
        self._avail = 1
        self._sel_row = None
        self._sel_file = ""
        self._sel_type = None
        self._sel_start = None
        self._sel_end = None

    def set_info(self, id, title, artist, end, pathname):
        #Takes in the file data, and updates the filegrid to represent
        #and indicate the files that are loaded with their metadata.
        from os.path import dirname, basename, splitext

        length = len(self.children)
        arg_list = [id, title, artist, end, basename(pathname), splitext(pathname)[1], pathname]

        if self._avail < length // self.cols:
            end = length - (self._avail * self.cols)
            start = end - self.cols
            for i, widget in enumerate(reversed(self.children[start:end])):
                widget.text = arg_list[i]
            self._avail += 1

        else:
            print("Full capacity.")


    #FileChooserMethods
    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filenames):
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

                self.set_info(id_num, title, artist, end_date, filename)


            except IOError:
                print("Cannot find file {}".format(filename))
            self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()




    #Widget detection
    def on_touch_up(self, touch):

        if  not self.collide_point(touch.x, touch.y):
            print("OVERRIDE ON TOUCH UP. PLS USE SUPER.")

        elif touch.is_double_tap and touch.button == 'left':
            #Load, double-click
            rows = len(self.children) // self.cols
            if self._avail < rows:
                print("Available slot: ", self._avail)
                self.show_load()
            else:
                print("No available slots.")
        else:
            #Single-click
            for row, widget in enumerate(reversed(self.children[::self.cols])):
                if touch.y >= widget.y:
                    if touch.button == 'left':
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
                    elif touch.button == 'right':
                        #implement right click for something
                        pass
                    break




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
