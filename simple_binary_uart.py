import PySimpleGUI as sg
import serial
from serial.tools import list_ports
import sys
import binascii
import time
#以下自作関数群
sys.path.append('./')
import crc_checker 

devices = None
buff = None
ser = None
file_name = None
read_file = None

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

def wait_ack(): #ACK待ち、正常：0xaa、異常：0x0f
    while True:
        uart_read()

        if (buff == 0xaa) or (buff == 0x0f):
            break
    return buff

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
    global file_name
    global read_file
    sg.theme('Default1')
    layout = [
        [sg.Combo((devices), size=(6, 1), key='com_combo'),sg.Button('ComOpen', key='com_button')], 
        [sg.InputText('ファイルを選択', enable_events=True,), sg.FilesBrowse('Select', key='open_file', file_types=(('txt ファイル', '*.txt'),))],
        [sg.ProgressBar(172, orientation='h', size=(35, 25), key='progressbar'), sg.Button('Write')],
        [sg.Text(key='info', size=(48, 1)),sg.Exit()]
    ]
    window = sg.Window('Simple Binary Uart Transport', layout, location = (400,200), finalize = True)
    progress_bar = window['progressbar']
    info = window["info"]
    info.update(value=f"COM closed")
    window['Write'].update(disabled=False)   
    toggle_com_button = True
    
    while True:
        event, values = window.read(timeout = 10, timeout_key = 'read_10ms')
        if event in (None, 'Exit'): #Exitが押されたらループを抜けて終了
            break
        if event == 'read_10ms':
            file_name = values['open_file']
            if toggle_com_button == False : #
                uart_read()
            if (toggle_com_button == False) and (len(file_name) > 0):   #UARTがオープン状態かつファイル名が有効の時にUARTへの出力を許可
                window['Write'].update(disabled=False)   
            else:
                window['Write'].update(disabled=True)   

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

        elif event == 'Write' :
            file_name = values['open_file']
            with open(file_name) as read_file:  #ファイル読み込み
                read_data = read_file.read()
                data_list = read_data.split(',')    #カンマ削除
                j = 0
                length = int((len(data_list)-1)/32) +1  #32byte区切りでの長さを格納
                data32 =[0] *length #リスト確保
                for i in range(len(data_list)): #'0x'と改行コードを削除
                    data_list[i] = data_list[i].replace('\n','')[2:]

                for i in range(0, len(data_list), 32):  #リストを32byte単位で結合する処理
                    data32[j] = ''.join(data_list[i:32+i])
                    if i == ((32*(int)(len(data_list)/32))):
                        data32[j] = data32[j] + '00'*24 #余った部分を0埋め　※画像サイズが異なる場合はココを修正する必要有り
                    j += 1

                for i in range((int)(len(data_list)/32+1)): #データ転送処理
                    header = 'a5'
                    header_and_datas = header + data32[i]   #ヘッダ付与
                    tx_crc = crc_checker.crc16_ccitt(text_2_bytes(header_and_datas))    #ヘッダ込みのデータのCRCを取得
                    tx_crc = hex(tx_crc)
                    tx_crc = tx_crc[2:].zfill(4)
                    tx_datas = header_and_datas + tx_crc    #ヘッダ・データ・CRCを結合
                    ser.write(text_2_bytes(tx_datas))   #データ転送
                    res = wait_ack()
                    if res == 0xaa:
                        info.update(value=str('Get Ack'))
                        #time.sleep(0.05)
                    elif res == 0x0f:
                        info.update(value=str('Repeat Req'))
                        time.sleep(0.1)
                        i -= 1
                    progress_bar.UpdateBar(i)   #プログレスバーに反映
                    if i == 172:
                        info.update(value=str('Transport finish'))
    window.close()

if __name__ == '__main__':
    ser = 0
    buff = 0
    ports = list_ports.comports()    # ポートデータを取得
    devices = [info.device for info in ports]
    main()