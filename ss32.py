from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty




class RootWidget(BoxLayout):

    def gib_args(*args):
        print(args)

    def edit_scot(f_name = '', **kwargs):
        #addr dict maps var names to
        #byte addresses and length

        #missing begin/end of audio, EOM, filename etc.
        addr = {"Title": (72, 43), "Year": (406, 4), "Artist": (335, 34),
                "Ending": (405, 1), "Note": (369, 34), "Start_Date": (133, 6),
                "End_Date": (139, 6), "Start_Hour": (145, 1), "End_Hour": (146, 1),
                }
        print(kwargs)




class GridFile(GridLayout):

    def set_info(self, title, artist, end, filename):


        arg_list = [title, artist, end, filename.split("\\")[-1], filename.split(".")[-1]]
        row = None
        for i, widget in enumerate(self.children[(-1 - self.cols)::-self.cols]):
            if not widget.text:
                row = i
                break
        if row != None:
            start = (-1 - self.cols - (row*self.cols))
            end = start - self.cols
            for i, widget in enumerate(self.children[start:end:-1]):
                widget.text = arg_list[i]
        else:
            print("We full.")


    #FileChooserMethods
    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        #print(path, filename)
        #self.load_text.text = filename[0]
        try:
            with open(filename[0], 'rb') as f:
                f.seek(72)
                title = f.read(43).decode("ascii")
                f.seek(335)
                artist = f.read(34).decode("ascii")
            self.set_info(title, artist, "31/07/2077", filename[0])


        except IOError:
            print("Cannot find file {}".format(filename[0]))
        self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()




    #Widget detection
    def on_touch_up(self, touch):
        if self.collide_point(touch.x, touch.y):
            num_rows = len(self.children) // self.cols

            #top row
            for widget in self.children[len(self.children) - self.cols:]:
                if widget.collide_point(touch.x, touch.y):
                    print(">Labels")
                    break
            else:
                #check for avail slots
                for row, widget in enumerate(self.children[(-1 - self.cols)::-self.cols]):
                    if not widget.text:
                        #load file popup menu
                        print("Available slot detected")
                        self.show_load()
                        break


        else:
            print("False positive.")



class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)





class SS32App(App):
    def build(self):
        return RootWidget()

if __name__ == '__main__':
    SS32App().run()
