import this
import PySimpleGUI as sg
from time import sleep, time
import threading
import random
import math

BACKGROUND_COLOR = 'grey'
PERIOD = float(2) # in seconds

updateValuesEventGeneratorRun = False
def updateValuesEventGenerator(window):
    while updateValuesEventGeneratorRun:
        window.write_event_value('-UPDATE_VALUES-', tuple())
        sleep(0.032)

windowMoveEventGeneratorRun = False
windowMoveEventTimer = 0.02
def windowMoveEventGenerator(window):
    while windowMoveEventGeneratorRun:
        window.write_event_value('-MOVE_WINDOW-', tuple())
        sleep(windowMoveEventTimer)


class coordinateProvider:
    def __init__(self, current_x, current_y, screen_w, screen_h, window_w, window_h, speed):
        self.current_x = float(current_x)
        self.current_y = float(current_y)
        self.max_x = screen_w - window_w
        self.max_y = screen_h - window_h - 90
        self.min_x = 0
        self.min_y = 0
        self.speed = speed
        self.angle = random.random() * 2 * math.pi - math.pi

    def setSpeed(self, speed):
        self.speed = speed
    
    def getx(self):
        if self.current_x >= self.max_x or self.current_x <= self.min_x:
            reflection_angle = -self.angle - math.pi
            self.angle=reflection_angle
            self.current_x = self.current_x + math.cos(self.angle) * self.speed
        self.current_x = self.current_x + math.cos(self.angle) * self.speed
        return int(self.current_x)

    def gety(self):
        if self.current_y >= self.max_y or self.current_y <= self.min_y:
            reflection_angle = self.angle * (-1)
            self.angle=reflection_angle
            self.current_y = self.current_y + math.sin(self.angle) * self.speed
        self.current_y = self.current_y + math.sin(self.angle) * self.speed
        return int(self.current_y)

def count_cps_and_to_string(start_time, end_time, number_of_clicks):
    time_diff = end_time - start_time
    if time_diff > 0:
        return str(round(number_of_clicks / time_diff, 3))
    else:
        return '0'

if __name__ == "__main__":
    random.seed(time())
    sg.theme('Reddit')

    sg.set_options(text_justification='left')   
    layout = [[sg.Column([[sg.Text("Cps: ", key='-CPS-')]]), sg.Column([[sg.Text("Average cps: ", key='-AVGCPS-')]])],
              [sg.Slider(range=(1, 20), key='-SPEED_SLIDER-', orientation='horizontal', enable_events=True)],
              [sg.Text("Time clicking: ", key='-TIME_CLICKING-')],
              [sg.Graph(canvas_size=(400, 200), graph_bottom_left=(-100,-50), graph_top_right=(100,50), background_color=BACKGROUND_COLOR, key='-CLICKING_AREA-', enable_events=True)]]
    window = sg.Window('Clicking Coach', layout, font=("Arial", 12), finalize=True)

    clicking_area = window['-CLICKING_AREA-']

    clicks_last_period = list() # timestamps of clicks that occured in last "period of time". Right now it's 2 seconds

    # coordinates of clicks that occured in last second-supposed to be synchronized with 'click_last_sec',
    # so that clicks_last_sec[i] = click_coord_last_sec[i]
    click_coord_last_sec = list()
    first_click_time = float() # time that is set when first click occurs
    last_click_time = float() # self explanatory
    click_count = 0 # self explanatory
    cProv = coordinateProvider(window.current_location()[0], window.current_location()[1],
                                window.get_screen_size()[0], window.get_screen_size()[1], window.Size[0], window.Size[1], 4)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == '-UPDATE_VALUES-':
            window['-AVGCPS-'].update('Average cps: ' + count_cps_and_to_string(first_click_time, last_click_time, click_count))
            if len(clicks_last_period) == 0:
                updateValuesEventGeneratorRun = False
                windowMoveEventGeneratorRun = False
                window['-TIME_CLICKING-'].update('Time clicking: ' + str(round(last_click_time - first_click_time, 3)))
                window['-CPS-'].update('Cps: 0')
            else:
                window['-TIME_CLICKING-'].update('Time clicking: ' + str(round(time() - first_click_time, 3)))
                window['-CPS-'].update('Cps: ' + count_cps_and_to_string(clicks_last_period[0], clicks_last_period[len(clicks_last_period) - 1], len(clicks_last_period)))

                deleted = []
                for i in range(len(clicks_last_period)):
                    time_since_click = time() - clicks_last_period[i]
                    if time_since_click > PERIOD:
                        deleted.append(i)

                for i in range(len(deleted)):
                    clicks_last_period.pop(0)
                    clicking_area.DrawCircle(click_coord_last_sec[0], 5, line_color=BACKGROUND_COLOR, fill_color=BACKGROUND_COLOR)
                    click_coord_last_sec.pop(0)

        elif event == '-MOVE_WINDOW-':
            window.move(cProv.getx(), cProv.gety())

        elif event == '-CLICKING_AREA-':
            last_click_time = time()
            if len(clicks_last_period) == 0:
                first_click_time = last_click_time
                click_count = 0
            click_count += 1
            clicks_last_period.append(last_click_time)
            click_coord_last_sec.append(values['-CLICKING_AREA-'])
            clicking_area.DrawCircle(values['-CLICKING_AREA-'], 5, line_color='red', fill_color='red')

            if not updateValuesEventGeneratorRun:
                updateValuesEventGeneratorRun = True
                updateThread = threading.Thread(target=updateValuesEventGenerator, args=[window])
                updateThread.setDaemon(True)
                updateThread.start()
            if not windowMoveEventGeneratorRun:
                windowMoveEventGeneratorRun = True
                wmThread = threading.Thread(target=windowMoveEventGenerator, args=[window])
                wmThread.setDaemon(True)
                wmThread.start()

        elif event == '-SPEED_SLIDER-':
            cProv.setSpeed(values['-SPEED_SLIDER-'])


    updateValuesEventGeneratorRun = False
    windowMoveEventGeneratorRun = False

    window.close()