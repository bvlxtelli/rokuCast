' rokuCast - components/MainScene.brs
' Receiver SceneGraph: toca URL direta via node Video.
' Inspirado no "sink" do MiracleCast: la o sink termina num
' pipeline gstreamer; aqui termina num content node do Roku.

sub init()
    m.top.backgroundURI = ""
    m.video = m.top.findNode("video")
    m.titleLabel = m.top.findNode("titleLabel")
    m.statusLabel = m.top.findNode("statusLabel")
    m.castTask = m.top.findNode("castTask")

    m.video.observeField("state", "onVideoState")
    m.castTask.observeField("media", "onBridgeMedia")

    m.bridgeUrl = ""
end sub

' Chamado via callFunc a partir de main.brs (launch inicial + roInputEvent tardio)
function handleLaunchArgs(args as dynamic) as boolean
    if args = invalid then return false

    url = firstOf(args, ["contentUrl", "mediaUrl", "url", "contentID"])
    if url <> invalid and url <> ""
        title = firstOf(args, ["title", "name"])
        if title = invalid then title = "Cast recebido"
        fmt = firstOf(args, ["streamFormat", "streamformat", "format"])
        if fmt = invalid then fmt = guessFormat(url)
        bridge = firstOf(args, ["bridgeUrl", "bridge"])
        if bridge <> invalid then setBridgeUrl(bridge)
        playUrl(url, fmt, title)
        return true
    end if

    ' So configurou o bridge (sem midia ainda): inicia polling
    bridge = firstOf(args, ["bridgeUrl", "bridge"])
    if bridge <> invalid
        setBridgeUrl(bridge)
        return true
    end if

    return false
end function

sub setBridgeUrl(url as string)
    m.bridgeUrl = url
    m.castTask.bridgeUrl = url
    m.castTask.control = "RUN"
    m.statusLabel.text = "Conectado ao bridge: " + url
end sub

sub onBridgeMedia(event as object)
    media = event.getData()
    if media = invalid then return
    url = media.url
    if url = invalid or url = "" then return
    fmt = media.streamFormat
    if fmt = invalid or fmt = "" then fmt = guessFormat(url)
    title = media.title
    if title = invalid or title = "" then title = "Cast recebido (bridge)"
    playUrl(url, fmt, title)
end sub

sub playUrl(url as string, fmt as string, title as string)
    content = CreateObject("roSGNode", "ContentNode")
    content.url = url
    content.title = title
    content.streamformat = fmt ' "hls" | "dash" | "mp4"

    m.video.visible = true
    m.video.content = content
    m.video.control = "play"
    m.titleLabel.text = title
    m.statusLabel.text = "Tocando: " + url
end sub

sub onVideoState(event as object)
    state = event.getData()
    if state = "error"
        m.statusLabel.text = "Erro ao tocar. Verifique URL/formato (hls/dash/mp4)."
    else if state = "finished"
        m.statusLabel.text = "Reproducao finalizada. Aguardando proximo cast…"
    end if
end sub

function guessFormat(url as string) as string
    l = LCase(url)
    if Instr(l, ".m3u8") > 0 then return "hls"
    if Instr(l, ".mpd") > 0 then return "dash"
    return "mp4"
end function

function firstOf(aa as object, keys as object) as dynamic
    for each k in keys
        if aa.DoesExist(k) and aa[k] <> invalid and aa[k] <> ""
            return aa[k]
        end if
    end for
    return invalid
end function
