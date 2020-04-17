import PySimpleGUI as sg
import serial
from serial.tools import list_ports
import sys
import binascii
#以下自作関数群
sys.path.append('./')
import crc_checker 

devices = None

def text_2_bytes(text_datas):  
    text_datas = text_odd_2_even(text_datas)
    text_datas = text_datas.encode('utf-8')
    return binascii.unhexlify(text_datas)

def text_odd_2_even(text_datas):
    if (len(text_datas) % 2) == 1 : #入力が奇数桁だった場合
        text_datas = '0' + text_datas
    return text_datas

def main():
    sg.theme('Default1')

    layout = [
        [sg.Combo((devices), size=(6, 1)),sg.Button('ComOpen')], 
        [sg.InputText('ファイルを選択', enable_events=True,), sg.FilesBrowse('Select', key='Open_file', file_types=(('txt ファイル', '*.txt'),))],
        [sg.ProgressBar(1000, orientation='h', size=(35, 25), key='progressbar'), sg.Button('Write')],
        [sg.T(' '*96),sg.Exit()]
    ]
    window = sg.Window('Simple Binary Uart Transport', layout, location = (400,200), finalize = True)
    progress_bar = window['progressbar']

    while True:
        event, values = window.read(timeout=1)

        for i in range(1000):
            progress_bar.UpdateBar(i)

        if event in (None, 'Exit'): #Exitが押されたらループを抜けて終了
            break


    window.close()

if __name__ == '__main__':
    #グローバル変数
    ser = 0
    buff = 0
 
    ports = list_ports.comports()    # ポートデータを取得
    devices = [info.device for info in ports]

    print(devices)
    print(type(devices))
    main()
    #GUI展開