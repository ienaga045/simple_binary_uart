import PySimpleGUI as sg
import serial
from serial.tools import list_ports
import sys
import binascii
#以下自作関数群
sys.path.append('./')
import crc_checker 

devices = None
buff = None
ser = None

def uart_connect(combo):  #UART接続
    global ser
    connect_state = True
    try :
        ser = serial.Serial(combo, '115200', timeout = 0.2, write_timeout = 0.2)
        connect_state = True
    except :
        connect_state = False

    return connect_state

def uart_close():   #UART切断
    global ser
    ser.close()
        
def uart_read():    #UART受信
    global buff
    global ser
    rx_length =ser.in_waiting
    if rx_length > 0:
        buff = int.from_bytes(ser.read(), byteorder='big') #シリアル受信バッファを取得
    else :
        buff = None

def text_2_bytes(text_datas):  
    text_datas = text_odd_2_even(text_datas)
    text_datas = text_datas.encode('utf-8')
    return binascii.unhexlify(text_datas)

def text_odd_2_even(text_datas):
    if (len(text_datas) % 2) == 1 : #入力が奇数桁だった場合
        text_datas = '0' + text_datas
    return text_datas

def main():
    global ser
    global buff
    sg.theme('Default1')

    layout = [
        [sg.Combo((devices), size=(6, 1), key='com_combo'),sg.Button('ComOpen', key='com_button')], 
        [sg.InputText('ファイルを選択', enable_events=True,), sg.FilesBrowse('Select', key='open_file', file_types=(('txt ファイル', '*.txt'),))],
        [sg.ProgressBar(1000, orientation='h', size=(35, 25), key='progressbar'), sg.Button('Write')],
        [sg.Text(key='info', size=(48, 1)),sg.Exit()]
    ]
    window = sg.Window('Simple Binary Uart Transport', layout, location = (400,200), finalize = True)

    progress_bar = window['progressbar']
    info = window["info"]
    info.update(value=f"COM closed")

    toggle_com_button = True
    file_name = None
    while True:
        event, values = window.read(timeout = 10, timeout_key = 'read_10ms')

        #for i in range(1000):
        #    progress_bar.UpdateBar(i)

        if event in (None, 'Exit'): #Exitが押されたらループを抜けて終了
            break

        if event == 'read_10ms':
            if toggle_com_button == False : #
                uart_read()
                if buff != None:
                    print(hex(buff))
                    if buff == 0xaa:
                        info.update(value=str('Get Ack'))
        elif event == 'com_button':   #COM openボタン押下時処理
            if toggle_com_button == True:
                uart_connection = uart_connect(values['com_combo'])
                if uart_connection == True:
                    toggle_com_button = not toggle_com_button
                    window['com_button'].update(('ComClose'))
                    info.update(value=f"COM open")
                else :
                    info.update(value=f"COM open fail")
            else :
                uart_close()
                toggle_com_button = not toggle_com_button
                window['com_button'].update(('ComOpen'))
                info.update(value=f"COM close")

        elif event == 'open_file':  
            file_name = values['open_file']
        
        elif event == 'Write' :
            header = 'a5'
            datas = '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f'
            tx_crc = crc_checker.crc16_ccitt(text_2_bytes(header + datas))
            tx_crc = hex(tx_crc)
            tx_crc = tx_crc[2:].zfill(4)
            tx_datas = header + datas + tx_crc
            print('heder + datas:' + header + datas)
            print('with crc:' + tx_datas)
            ser.write(text_2_bytes(tx_datas))

    window.close()

if __name__ == '__main__':
    ser = 0
    buff = 0
 
    ports = list_ports.comports()    # ポートデータを取得
    devices = [info.device for info in ports]

    main()