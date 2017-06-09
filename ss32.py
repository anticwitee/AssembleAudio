
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import parse_kivy

class SS32(GridLayout):

    def Convert(self, m_title, m_artist, m_id, m_why_not):
        print(self, m_title, m_artist, m_id, m_why_not)

        parse_kivy.ConvertScott(m_why_not, "SP" + m_id + ".wav", m_title, m_id, m_artist)


class SS32App(App):

    def build(self):
        return SS32()


if __name__ == '__main__':
    SS32App().run()
