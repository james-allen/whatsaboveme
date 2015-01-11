import kivy
kivy.require('1.8.0')

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

import numpy as np


Builder.load_string("""
<HomeScreen>:
    BoxLayout:
        orientation: 'vertical'
        Button:
            text: "What's above me?"
            on_release: root.manager.current = 'wam_now'

<WamNowScreen>:
    on_enter: self.refresh_results()
    BoxLayout:
        orientation: 'vertical'
        Label:
            id: results
            text: 'Results go here'
        Button:
            text: 'Back to menu'
            on_release: root.manager.current = 'home'
""")


class HomeScreen(Screen):
    pass

class WamNowScreen(Screen):
    def refresh_results(self):
        self.ids.results.text = repr(np.arange(3))

sm = ScreenManager()
sm.add_widget(HomeScreen(name='home'))
sm.add_widget(WamNowScreen(name='wam_now'))


class WamApp(App):

    def build(self):
        return sm


if __name__ == '__main__':
    WamApp().run()
