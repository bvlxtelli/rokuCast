' rokuCast - source/main.brs
' Entry point do channel. Recebe args de DIAL / ECP / Voice launch
' via roInputEvent (supports_input_launch=1 no manifest).
'
' Formatos aceitos (todos opcionais):
'   contentUrl  ou mediaUrl ou url  -> URL direta (mp4/m3u8/mpd)
'   streamFormat -> "hls" | "dash" | "mp4" (auto-detect pela extensao)
'   title, subtitle
'   bridgeUrl   -> http://<bridge>:8010  (para polling da fila CastTask)
'   deviceName

sub main(args as dynamic)
    screen = CreateObject("roSGScreen")
    if screen = invalid then return

    port = CreateObject("roMessagePort")
    screen.setMessagePort(port)

    scene = screen.CreateScene("MainScene")
    screen.show()

    ' Repassa args de launch (DIAL/ECP) para a cena
    if args <> invalid and GetInterface(args, "ifAssociativeArray") <> invalid
        scene.callFunc("handleLaunchArgs", args)
    end if

    ' Loop principal: despacha roInputEvent (lancamentos tardios via ECP)
    ' Ex: curl -d "" "http://ROKU:8060/launch/dev?contentUrl=http%3A%2F%2F...&title=Teste"
    while true
        msg = wait(0, port)
        if type(msg) = "roSGScreenEvent"
            if msg.isScreenClosed() then return
        else if type(msg) = "roInputEvent"
            info = msg.GetInfo()
            if info <> invalid
                scene.callFunc("handleLaunchArgs", info)
            end if
        end if
    end while
end sub
