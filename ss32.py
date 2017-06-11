
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
import parse_kivy

class SS32(GridLayout):

    loadfile = ObjectProperty(None)
    media_why_not = ObjectProperty(None)

    def Convert(self, source, m_id, title, artist):
        print(self, source, m_id, title, artist)
        from os import chdir
        t_path = source.split('\\')
        path = "\\".join(t_path[:-1])
        print(path)

        chdir(path)
        parse_kivy.ConvertScott(source, "SP" + m_id + ".wav", title, m_id, artist)


    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        if True:
            self.load_text.text = filename[0]
        else:
            with open(os.path.join(path, filename[0])) as stream:
                self.text_input.text = stream.read()

        self.dismiss_popup()

    def dismiss_popup(self):
        self._popup.dismiss()


class SS32App(App):

    def build(self):
        return SS32()


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)



if __name__ == '__main__':
    SS32App().run()
