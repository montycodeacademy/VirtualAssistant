import os
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem
from kivy.lang import Builder

from kivy.clock import Clock

from plyer import tts
from gtts import gTTS
from playsound import playsound
import speech_recognition as sr

from random import randint

import requests

from noaa_sdk import NOAA

KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: 20
    
    ScrollView:
        MDList:
            id: list_text_box
              
    BoxLayout:
        orientation: 'horizontal'
        MDTextField:
            id: text_to_convert
            hint_text: "Type and hit play / Click on Mic and Speak"
            multiline: False
            on_text_validate: app.text_validate()
            on_text: app.text_update()
    
        MDIconButton:
            id: play_button
            disabled: True
            icon: "play"
            on_release: app.text_validate()
        
        MDIconButton:
            id: mic_button
            icon: "microphone"
            on_release:
                app.get_text_from_mic()
'''



class VoiceAssistApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        self.root = Builder.load_string(KV)

    def speak_text(self, text = ''):
        if len(text) < 1:
            text = self.root.ids.text_to_convert.text
        try:
            tts.speak(text)
        except NotImplementedError:
            if os.path.exists("output.mp3"):
                try:
                    os.remove("output.mp3")
                    print("output.mp3" + "deleted")
                except OSError:
                    return
            language = 'en'
            output = gTTS(text = text,
                          lang = language,
                          slow = False)

            output.save("output.mp3")
            playsound("output.mp3")

        self.root.ids.play_button.disabled = True
        self.root.ids.mic_button.disabled = False
        newListItem = OneLineListItem()
        newListItem.text = text
        self.root.ids.list_text_box.add_widget(newListItem)
        self.root.ids.text_to_convert.text = ""

    def record_text_and_respond(self, text, response):
        newListItem = OneLineListItem()
        newListItem.text = text
        self.root.ids.list_text_box.add_widget(newListItem)
        self.root.ids.text_to_convert.text = ""
        self.speak_text(text=response)

    def text_validate(self):
        self.root.ids.play_button.disabled = False
        text = self.root.ids.text_to_convert.text
        copyText = text.lower()
        query_handled = False
        if 'name' in copyText:
            if 'what' in copyText:
                self.record_text_and_respond(text, "Hello, my name is Andy")
                query_handled = True
            elif 'my' in copyText:
                mywordlist = copyText.split(' ')
                self.record_text_and_respond(text, "Glad to meet you " + mywordlist[-1] + " how are you?")
                query_handled = True
        elif 'how' in copyText and 'are' in copyText and "you" in copyText:
            self.record_text_and_respond(text, "I am doing wonderful, thank you for asking")
            query_handled = True
        elif ("what" in copyText or 'gimme' in copyText) \
                    and ("lucky" in copyText and "number" in copyText):
            number = randint(0, 100)
            self.record_text_and_respond(text, "My Lucky Number is " + str(number))
            query_handled = True
        elif "weather" in copyText:
            '''get weather for your location'''
            self.noaa = NOAA()
            responses = self.noaa.points_forecast(34.0522, -118.2437, type='forecastGridData')
            response_text = "The weather forecast is "
            weather_failed = False

            for item in (responses['properties']['weather']['values'][0]['value']):
                if item['intensity'] != None:
                    response_text = response_text + item['coverage'] + " "
                    response_text = response_text + item['intensity'] + " "
                    response_text = response_text + item['weather'] + " "
                weather_failed = True

            if weather_failed:
                response_text = "National Oceanic and Atmospheric Administration is offline, please try later "

            self.record_text_and_respond(text, response_text)
            query_handled = True


        if not query_handled:
            response = requests.get("https://api.duckduckgo.com",
                         params={
                             "q": text,
                             "format": "json"
                         })

            data = response.json()
            responseText = "I do not have an Answer for that"
            print(data)
            if len(data['AbstractText']):
                responseText = data['AbstractText']
            elif len(data['RelatedTopics']):
                field = data['RelatedTopics'][0]
                responseText = field["Text"]

            responseText = responseText[0:responseText.find('.')]
            self.record_text_and_respond(text, responseText)

    def text_update(self):
        self.root.ids.play_button.disabled = len(self.root.ids.text_to_convert.text) < 1


    def get_text_from_mic(self):
        self.root.ids.mic_button.disabled = True
        Clock.schedule_once(self.listen_and_record)
        return


    def listen_and_record(self, st):
        sp_recog = sr.Recognizer()
        text_said = ""
        with sr.Microphone() as source:
            audio = sp_recog.listen(source)
            try:
                text_said = sp_recog.recognize_google(audio)
                self.root.ids.text_to_convert.text = text_said
                self.text_validate()

            except Exception as e:
                print("Exception" + str(e))

    def capture(self):
        print("Capture Image")




if __name__ == '__main__':
    myApp = VoiceAssistApp()
    myApp.run()