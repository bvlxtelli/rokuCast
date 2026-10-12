' rokuCast - components/CastTask.brs
' Polling simples contra o bridge: GET {bridgeUrl}/queue/next?clear=1
' Resposta JSON esperada: {"url":"...","streamFormat":"hls","title":"..."}
' ou {"url":""} quando nao ha nada novo.
' BrightScript nao tem server-socket confiavel p/ CastV2, por isso o
' bridge (Python, fora da TV) faz discovery/anuncio e a TV apenas consome.

sub init()
    m.top.functionName = "pollLoop"
end sub

sub pollLoop()
    lastUrl = ""
    while true
        bridge = m.top.bridgeUrl
        if bridge = invalid or bridge = "" then
            sleep(2000)
        else
            media = fetchNext(bridge)
            if media <> invalid and media.url <> invalid and media.url <> "" and media.url <> lastUrl
                lastUrl = media.url
                m.top.media = media
            end if
            sleep(2000)
        end if
    end while
end sub

function fetchNext(bridge as string) as dynamic
    xfer = CreateObject("roUrlTransfer")
    xfer.SetCertificatesFile("common:/certs/ca-bundle.crt")
    xfer.AddHeader("Accept", "application/json")
    xfer.SetUrl(bridge + "/queue/next?clear=1")
    xfer.SetTimeout(8)
    body = xfer.GetToString()
    if body = invalid or body = "" then return invalid
    json = ParseJson(body)
    if json = invalid then return invalid
    if json.url = invalid or json.url = "" then return invalid
    return {
        url: json.url
        streamFormat: ifString(json, "streamFormat")
        title: ifString(json, "title")
    }
end function

function ifString(aa as object, key as string) as string
    if aa.DoesExist(key) and aa[key] <> invalid then return aa[key]
    return ""
end function
