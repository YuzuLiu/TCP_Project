import kivy
import os
from client import *
from threading import Thread
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from os.path import join, getsize
from kivy.core.window import Window
from kivy.uix.recycleview import RecycleView
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.popup import Popup
import time

kivy.require("1.11.1")

choosen_music = ''

class LoginScreen(Screen):
    def login(self, username):
        self.s = MySocket()
        self.s.send_username(username)
        Thread(target=self.get_data).start()

    def get_data(self):
        while True:
            self.text = self.s.get_data().decode('utf-8')
            if self.text == 'Yes':
                self.manager.current = 'user_screen'
                
                with open('project.ini', 'w') as f:
                    f.write('[login]\nusername = ' + self.ids.login_username.text)
                    f.close()

            elif self.text == 'No':
                self.ids.input_warning.color = 1,0,0,1
                pass
                
    pass

class UserScreen(Screen):
    def get_gifts(self):
        with open('upload_number.txt', 'r') as f:
            upload_number = f.readline().rstrip()
            f.close()
        if int(upload_number) == -1:
            self.manager.current = 'gifts_screen'
        if int(upload_number) >= 0:
            self.s = MySocket()
            self.s.sock.sendall('Exchange {}'.format(upload_number).encode('utf-8'))
            while True:
                self.filename = self.s.sock.recv(128).decode('utf-8')
                if self.filename.endswith('.mp3'):
                    f = open('gifts.txt', 'a+')
                    f.write(self.filename + '\n')
                    f.close()
                print('Going to gifts screen')
                with open('upload_number.txt', 'w+') as f:
                    f.write('-1')
                    f.close()
                break
        self.manager.current = 'gifts_screen'

    def go_rating_screen(self):
        with open('music_rating.txt', 'w+') as f:
            self.s = MySocket()
            self.s.sock.sendall('100 1'.encode('utf-8'))
            self.musicRate = self.s.sock.recv(1024).decode('utf-8')
            if self.musicRate =='No':
                f.close()
                self.manager.current = 'rating_screen'
            else:
                f.write(self.musicRate)
                f.close()
        self.manager.current = 'rating_screen'
    pass

class RatingScreen(Screen):
    pass

class GiftScreen(Screen):
    def music_info_pop(self):
        box = BoxLayout(orientation = 'vertical', padding = (10)) 
        box.add_widget(Label(text = "You can choose to download the music\n or rate the music.\n (Press anywhere to leave)")) 
        btn1 = Button(text = "Rate Music") 
        btn2 = Button(text = "Download") 
        box.add_widget(btn1) 
        box.add_widget(btn2) 

        popup = Popup(title=choosen_music, title_size= (30), 
            title_align = 'center', content = box, 
            size_hint=(None, None), size=(400, 400), 
            auto_dismiss = True) 

        btn1.bind(on_press = self.rate)
        btn2.bind(on_press = self.download)
        popup.open() 

    def rate(self, *args):
        pop = OpenRate(self)
        pop.open()
        pass

    def download(self, *args):
        self.s = MySocket()
        self.s.sock.sendall('Downloading {}'.format(choosen_music).encode('utf-8'))
        f = open(choosen_music, 'wb')
        print('Filename: ' + choosen_music)
        while True:
            print('Waiting for filesize...')
            size = self.s.sock.recv(4)

            res = 0
            for i in range(4):
                res += size[i] << (i*8)
            size = res

            print('Total size: ' + str(size))
            current_size = 0
            buffer = b""
            while current_size < size:
                data = self.s.sock.recv(1024)
                if not data:
                    print('Breaking...')
                    break
                if len(data) + current_size > size:
                    data = data[:size-current_size]
                buffer += data
                current_size += len(data)
                f.write(data)
            break
        print('File Received')
        f.close()
            
        pass
    pass

class OpenRate(Popup):

    _score = NumericProperty()
    error = StringProperty()

    def __init__(self, parent, *args):
        super(OpenRate, self).__init__(*args)

    def on_error(self, inst, text):
        if text:
            self.lb_error.size_hint_y = 1
            self.size = (400, 150)
        else:
            self.lb_error.size_hint_y = None
            self.lb_error.height = 0
            self.size = (400, 120)

    def _enter(self):
        if int(self.text) < 1 or int(self.text) > 5:
            self.error = "Error: enter score between 1 to 5"
        else:
            self.s = MySocket()
            self.s.sock.sendall('{} {}'.format(self.text, choosen_music).encode('utf-8'))
            self.dismiss()

    def _cancel(self):
        self.dismiss()

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''


class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            print("selection changed to {0}".format(rv.data[index]))
            global choosen_music
            choosen_music = str(rv.data[index].get('text'))
            
        else:
            print("selection removed for {0}".format(rv.data[index]))


class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        gifts = []
        with open('gifts.txt', 'a+') as f:
            f.seek(0)
            music = f.readline().rstrip()
            while music:
                gifts.append(music)
                music = f.readline().rstrip()
            f.close()
        self.data = [{'text': str(x)} for x in gifts]
    
class RV_rate(RecycleView):
    def __init__(self, **kwargs):
        super(RV_rate, self).__init__(**kwargs)
        rating_data = []
        with open('music_rating.txt', 'a+') as f:
            f.seek(0)
            rating = f.readline().rstrip()
            while rating:
                rating_data.append(rating)
                rating = f.readline().rstrip()
            f.close()
        self.data = [{'text': str(x)} for x in rating_data]

class FileChooserScreen(Screen):
    def select(self, *args): 
        try:
            self.label.text = args[1][0]
        except:
            pass

    def convert_to_bytes(self, no):
        result = bytearray()
        result.append(no & 255)
        for i in range(3):
            no = no >> 8
            result.append(no & 255)
        return result

    def button_press(self, musicPath):
        Thread(target=self.sendFile, args=(musicPath,)).start()
        self.manager.current = 'user_screen'

    def sendFile(self, musicPath):
        if musicPath.endswith('.mp3'):
            self.s = MySocket()
            self.s.sock.sendall('Uploading {}'.format(musicPath).encode('utf-8'))
            while True:
                self.text = self.s.sock.recv(32).decode('utf-8')
                if self.text == 'getfile':
                    length = os.path.getsize(musicPath)
                    self.s.sock.sendall(self.convert_to_bytes(length))
                    with open(musicPath, 'rb') as f:
                        data = f.read(1024)
                        while data:
                            self.s.sock.sendall(data)
                            data = f.read(1024)
                        f.close()

                    upload_number = self.s.sock.recv(32).decode('utf-8')
                    with open('upload_number.txt', 'w') as f:
                        f.write(upload_number)
                        f.close()
                    
    pass

class MainScreen(ScreenManager):
    pass

class projectApp(App):
    def build_config(self, config):
        config.setdefaults('login', {'username': ''})

    def set_username(self, username):
        self.config.set('login', 'username', username)
        self.config.write()

    def build(self):
        config = self.config
        self.username = config.get('login', 'username')

        self.root = MainScreen()

        if self.username == '':
            self.root.current = 'login_screen'
        else:
            self.root.current = 'user_screen'

projectApp().run()