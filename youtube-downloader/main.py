import FreeSimpleGUI as sg
from pytubefix import YouTube
# import json








def check_soemthing(cccc,values):
    kkk =[]
    for i in values:
        if values[i] == True:
            ii =str(i)
            cc = (cccc[int(i)])
            print("Downloaded"+' '+ii+" "+cc)
            stringg = cc.split(",")
            kkk.append(stringg)
            break
    # print(kkk[0])
    return kkk[0]







def download_1(tag,pathss,ty):
    yt = YouTube(ty)
    ta = tag[0]
    yt.streams.get_by_itag(ta).download(pathss)
    print("Downloaded "+yt.title +" at "+pathss)
    sg.popup("Downloaded "+yt.title +" at "+pathss)



def select_download(llliinkk,pathss):
    yt = YouTube(llliinkk)
    dd = yt.streams
    cccc = []
    layout1=[]
    d = 0
    fps= 'N/A'
    # print(dd)
    for i in dd:
        d += 1
        if i.type == "video":
            fps = i.fps
        else:
            fps = "N/A"
        
        layout1.append([sg.Text(i.resolution),sg.Text(i.mime_type),sg.Text(i.itag),sg.Text(i.filesize),sg.Radio('Download!', group_id=1)])
        cont=f"{str(i.itag)},{str(i.mime_type)},{str(i.resolution)},{str(fps)},{str(i.codecs)},{str(i.is_progressive)},{str(i.abr)},{str(i.type)},{d}"
        cccc.append(cont)
        # layout = [[sg.Radio('My first Radio!', group_id=1, default=True)]]

    layout1.append([sg.Exit(),sg.Submit()])
    # print(cccc)
    window1 = sg.Window("Title", layout1,modal=True)

    while True:
        event, values = window1.read()
        if event == sg.WIN_CLOSED or event == "Exit":
            break
        if event == "Submit":
            # print(values)
            pat = pathss
            arr = check_soemthing(cccc,values)
            download_1(arr,pat,llliinkk)

            # print(event)

            break
    window1.close()
        







sg.theme('DarkTeal9')
# Define the window's layout
layout = [
    [sg.Text("Youtube Link :"), sg.InputText(key="input1")],
    [sg.Text("PATH :"), sg.InputText(key="input2"),sg.FolderBrowse()], 
    [sg.Exit(), sg.Button("OK")]
]

winodw = sg.Window("Title", layout)

while True:
    event, values = winodw.read()
    if event == sg.WIN_CLOSED or event == "Exit":
        break
    if event == "OK":
        # data = download_video(link = values["input1"])
        select_download(values["input1"],values["input2"])
        # sg.popup_scrolled(data)
        

winodw.close()




