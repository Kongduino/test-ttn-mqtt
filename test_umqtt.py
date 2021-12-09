import time, network, ujson, ubinascii, gui, gc
from umqtt.simple2 import MQTTClient
from machine import Pin
import usocket
from uselect import select
from neopixel import NeoPixel
from tftlcd import LCD32

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (178, 180, 181)
ORANGE =(0xFF, 0x7F, 0x00)
YELLOW =(0xFF, 0xFF, 0x00)
INDIGO =(0x4B, 0x00, 0x82)
neoColors = [RED, ORANGE, YELLOW, GREEN, BLUE, INDIGO, WHITE]
clIndex = 0
neo = Pin(3, Pin.OUT)
np = NeoPixel(neo, 1)
LED = Pin(2, Pin.OUT)
KEY = Pin(0, Pin.IN, Pin.PULL_UP)
py = 5

secretsFile = 'wifisecret.json'
naeyong = "No message so far!"
sox = 0
mqtt_user = ''
mqtt_password = ''
packetCount = 0
html = """HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
    <head><title>ESP32 MQTT Server</title></head>
    <body><h1>Last Message</h1><h2>response</h2>
    </body>
</html>
"""
d = LCD32(portrait=1)

def Color_buf(color):
    np[0]=color
    np.write()

def client_handler(client):
    global naeyong
    response = html.replace('response', naeyong)
    client.send(response)
    time.sleep(1)
    client.close()

def WIFI_Connect():
    global mqtt_user, mqtt_password, sox, d, secretsFile, BLACK, WHITE, py
    d.fill(WHITE)
    d.printStr("Starting wifi...", 5, py, BLACK, size=2)
    py += 30
    gc.collect()
    d.printStr("* getting credentials", 10, py, BLACK, size=1)
    py += 17
    with open(secretsFile) as fp:
        data = ujson.loads(fp.read())
    fp.close()
    mqtt_user = data['mqtt_user']
    mqtt_password = data['mqtt_password']
    d.printStr("* initializing", 10, py, BLACK, size=1)
    py += 17
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    start_time=time.time()
    if not wlan.isconnected():
        print('Cconnecting to network '+data['SSID']+'...')
        d.printStr('* Connecting to '+data['SSID']+'...', 10, py, BLACK, size=1)
        py += 17
        wlan.connect(data['SSID'], data['pwd'])
        while not wlan.isconnected():
            LED.value(1)
            time.sleep_ms(300)
            LED.value(0)
            time.sleep_ms(300)
            if time.time()-start_time > 15 :
                print('WIFI connection timeout!')
                d.printStr('WIFI connection timeout!', 10, py, BLACK, size=1)
                py += 17
                break
    if wlan.isconnected():
        LED.value(1)
        print('Network information:')
        print(' IP: '+wlan.ifconfig()[0])
        print(' Subnet: '+wlan.ifconfig()[1])
        print(' GW: '+wlan.ifconfig()[2])
        d.printStr('Network information:', 5, py, BLACK, size=1)
        py += 17
        d.printStr('* IP: '+wlan.ifconfig()[0], 10, py, BLACK, size=1)
        py += 17
        d.printStr('* Subnet: '+wlan.ifconfig()[1], 10, py, BLACK, size=1)
        py += 17
        d.printStr('* GW: '+wlan.ifconfig()[2], 10, py, BLACK, size=1)
        py += 17
        addr = usocket.getaddrinfo(wlan.ifconfig()[0], 80)[0][-1]
        sox = usocket.socket()
        sox.bind(addr)
        sox.listen(1)
        print('Listening on', addr)
        d.printStr('Listening on '+addr[0]+':'+str(addr[1]), 5, py, BLACK, size=1)
        py += 33

# Received messages from subscriptions will be delivered to this callback
def sub_cb(topic, msg, retain, dup):
    global packetCount, naeyong, py
    #print((topic, msg, retain, dup))
    packet = ujson.loads(msg)
    if "uplink_message" in packet.keys():
        Color_buf(GREEN)
        LED2=Pin(2, Pin.OUT)
        LED2.value(1)
        time.sleep(0.2)
        LED2.value(0)
        time.sleep(0.2)
        LED2.value(1)
        time.sleep(0.2)
        LED2.value(0)
        time.sleep(0.2)
        LED2.value(1)
        packetCount += 1
        print("* Message "+str(packetCount)+" received:")
        u=packet["uplink_message"]
        rx=u["rx_metadata"]
        msg = ubinascii.a2b_base64(u["frm_payload"]).decode()
        savePy = py
        for i in range(80):
            d.drawLine(0, py+i+2, 240, py+i+2, WHITE)
        d.printStr("* "+msg, 10, py, BLUE, WHITE, size=1)
        py += 17
        d.printStr("* RSSI: "+str(rx[0]['rssi'])+", SNR: "+str(rx[0]['snr']), 10, py, BLUE, WHITE, size=1)
        py += 17
        d.printStr("* Gateway:", 10, py, BLUE, WHITE, size=1)
        py += 17
        d.printStr("  "+rx[0]['gateway_ids']['gateway_id'], 10, py, BLUE, WHITE, size=1)
        py += 17
        d.printStr("* Packet count:"+str(packetCount), 10, py, BLUE, WHITE, size=1)
        py = savePy
        print(" > "+msg)
        print(" > RSSI: "+str(rx[0]['rssi'])+", SNR: "+str(rx[0]['snr']))
        print(" > Gateway: "+rx[0]['gateway_ids']['gateway_id'])
        naeyong="<ul><li>Message: "+msg+"</li><li>RSSI: "+str(rx[0]['rssi'])+", SNR: "+str(rx[0]['snr'])
        naeyong += "</li><li>Gateway: "+rx[0]['gateway_ids']['gateway_id']+"</li>"
        naeyong += "<li>Packet count: "+str(packetCount)+"</li></ul>"
    Color_buf(INDIGO)

def main(server="eu1.cloud.thethings.network"):
    global mqtt_user, mqtt_password, sox, BLACK, WHITE, py
    print("Let's start with wifi, prefs file "+secretsFile)
    WIFI_Connect()
    print("Starting MQTT client...")
    d.printStr("Starting MQTT...", 5, py, BLACK, size=2)
    py += 30
    c = MQTTClient("umqtt.simple2", server, user = mqtt_user, password = mqtt_password)
    c.set_callback(sub_cb)
    print("* Connecting...")
    d.printStr("* Connecting...", 10, py, BLACK, size=1)
    py += 17
    c.connect()
    print("* Subscribing...")
    d.printStr("* Subscribing...", 10, py, BLACK, size=1)
    c.subscribe(b"#")
    print("Done...")
    d.printStr("Done!", 140, py, BLACK, size=1)
    py += 17
    while True:
        try:
            c.check_msg()
            r, w, err = select((sox, ), (), (), 1)
            if r:
                for readable in r:
                    cl, addr = sox.accept()
                    try:
                        client_handler(cl)
                    except OSError as e:
                        pass
        except:
            pass
    c.disconnect()
    LED2.value(0)

if __name__ == "__main__":
    d.fill(BLACK)
    d.printStr("MQTT Client", 5, 5, WHITE, size=3)
    count = 0
    total = 5000
    while count < 5:
        Color_buf(neoColors[clIndex])
        clIndex += 1
        print("Launching in "+str(5-count)+" sec")
        d.printStr("Launching in "+str(5-count)+" sec", 10, 60+count*15, WHITE, size=1)
        count += 1
        cnt = 1000
        while cnt>0:
            time.sleep_ms(10)
            cnt -= 10
            if KEY.value()==0:
                secretsFile = 'wifiphonesecret.json'
                print("Switching to phone!")
                cnt = 0
                count = 6
    main()
