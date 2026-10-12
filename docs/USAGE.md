# Como usar o rokuCast — guia de consumo

Passo a passo para sair do zero até o vídeo tocando na TV. O app não traz
nenhuma mídia: você traz a sua URL (MP4/HLS/DASH sem DRM) e o rokuCast leva
ela até a TV.

## 0. O que você precisa

-   TV Roku e celular/PC **no mesmo Wi-Fi**.
-   IP do Roku (TV: Configurações → Rede → Sobre).
-   Um PC ou Raspberry na mesma rede para rodar o bridge.
-   Suas URLs de mídia (arquivo `.mp4`, live `.m3u8`, etc.).

## 1. Instalar o channel na TV (uma vez só)

> Caminho fácil: baixe o `rokuCast-channel-vX.Y.Z.zip` pronto na página
> [Releases](https://github.com/bvlxtelli/rokuCast/releases/latest) e pule
> para o passo 3.
>
> Caminho manual (só se quiser montar o zip você mesmo):
>
> 1.  No PC, compacte **o conteúdo** de `roku-channel/` num `.zip`
>     (o `manifest` tem que ficar na raiz do zip).

2.  Ative o modo desenvolvedor do Roku: no controle, `Home 3x, Up 2x,
    Right, Left, Right, Left, Right`. Anote o IP e a senha que aparecer.
3.  Abra `http://<IP-DO-ROKU>/` no navegador, entre com `rokudev` + a senha.
4.  Suba o `.zip` pelo instalador e aguarde a TV abrir o channel **rokuCast**.
5.  Deixe o channel **aberto na TV** — ele só recebe cast em primeiro plano.

## 2. Rodar o bridge (toda vez que for usar)

```bash
uv run rokucast --roku-ip 192.168.1.50 --name "Sala (Roku)"
```

-   Sem `uv`? `pip install -e .` e depois `rokucast --roku-ip ...`.
-   Para a TV aparecer no menu Cast do Android/Chrome, instale o extra uma vez:
    `uv pip install -e ".[mdns]"`.
-   Confira no navegador: `http://localhost:8010/status`.

## 3. Mandar sua primeira mídia

```bash
curl -X POST http://localhost:8010/cast ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://SEU_VIDEO.m3u8\",\"title\":\"Demo\"}"
```

A TV toca em segundos. O bridge tenta um push imediato (ECP) e a fila
(`GET /queue/next`, consultada pelo channel a cada 2 s) cobre qualquer falha.

Contrato do `/cast`:

| Campo | Obrigatório | Explicação |
|---|---|---|
| `url` | sim | URL direta que **o Roku alcança** (`http(s)://...`) |
| `title` | não | Nome exibido na TV |
| `streamFormat` | não | `hls`, `dash` ou `mp4` (detectado da URL se omitido) |

## 4. Arquivos locais (VLC, MP4 do PC ou do celular)

O Roku baixa a URL sozinho — arquivo parado no celular/PC ele não enxerga.
Sirva por HTTP primeiro:

```bash
# no PC, pasta com os vídeos:
python -m http.server 8080 --directory "E:\Videos"

# depois mande o IP DO PC (não localhost):
curl -X POST http://localhost:8010/cast ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"http://192.168.1.20:8080/filme.mp4\",\"title\":\"Filme\"}"
```

No Android, use um app que sirva HTTP (ex. Material Files, servidor do
BubbleUPnP/LocalCast) ou que envie URLs para endpoints (Web Video Caster
apontando para `http://<bridge>:8010/cast`).

> O botão Cast de apps como VLC/YouTube **não vai listar** o rokuCast:
> eles exigem o protocolo CastV2 completo, que o bridge não implementa de
> propósito. O caminho é o `POST /cast` acima.

## 5. O que funciona e o que não funciona

Funciona: MP4 (H.264+AAC é 100%), HLS (`.m3u8`), DASH (`.mpd`), IPTV sem
token, links do Jellyfin/Plex, câmeras/lives sem DRM. MKV/H.265/legendas
dependem do modelo do Roku — se falhar, converta para MP4/HLS antes.

Não funciona (resposta `501` honesta, sem gambiarra): Netflix, Prime,
Disney+, YouTube logado e qualquer app com DRM. Para esses, use o app
nativo do Roku. Espelhamento de tela? Use o Espelhamento nativo do Roku
(Configurações → Sistema → Espelhamento de tela), nunca este bridge.

## 6. Problemas comuns

| Sintoma | Cheque |
|---|---|
| TV não toca nada | Channel aberto na TV? Mesmo Wi-Fi? `GET /status` mostra a fila crescendo? |
| `curl` conecta mas TV não reage | IP do Roku mudou (DHCP)? Teste ECP direto: `curl -d "" "http://<ROKU>:8060/query/device-info"` |
| Erro ao tocar na TV | Formato suportado? URL acessível **do Roku** (teste no PC com `curl -I <url>`)? |
| Não aparece no menu Cast | Extra `mdns` instalado? Alguns roteadores bloqueiam multicast — use o `POST /cast` manual |
| Vídeo trava | Rede 2.4 GHz fraca? Prefira 5 GHz ou HLS com bitrate menor |

Travou de verdade? [Abra uma issue](https://github.com/bvlxtelli/rokuCast/issues)
com o log do bridge + a saída de `GET /status` (sem URLs privadas, por favor).
