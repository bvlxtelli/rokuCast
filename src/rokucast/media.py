"""Media helpers: format guessing + the MiracleCast WFD mapping."""

from __future__ import annotations


def guess_format(url: str) -> str:
    """Map a media URL to a Roku Video `streamformat`."""
    u = url.lower()
    if ".m3u8" in u:
        return "hls"
    if ".mpd" in u:
        return "dash"
    return "mp4"


class MiracleTranslator:
    """Documents the WFD (Miracast) -> Roku mapping.

    MiracleCast's `sinkctl run` does, behind the scenes:
      M1 GET_PARAMETER (wfd_audio_codecs, wfd_video_formats, ...)
      M2 OPTIONS / M3 GET_PARAMETER (sink answers)
      M4 SET_PARAMETER (sink -> source: accepted formats)
      M5 TRIGGER SETUP / M6 SETUP (RTP ports, presentation URL)
      M7 PLAY -> RTP/MPEG2-TS H.264 -> gstreamer viewer.

    Roku exposes no Wi-Fi P2P and no RTP port decodable via BrightScript,
    so the only supported mapping is *media-by-URL*:

      wfd_presentation_URL rtsp://.../wfd1.0/streamid=0 -> NOT directly playable
      wfd_video_formats (H264 1080p60)                  -> Video.streamformat
      wfd_audio_codecs (AAC/LPCM)                       -> Video.audioTrack (auto)
      TRIGGER TEARDOWN                                  -> Video.control=stop
      UIBC back-channel                                 -> ECP keypress (Up/Down/OK/...)

    Live screen mirroring (MPEG-TS) is NOT converted: use the Roku's native
    Screen Mirroring (official Miracast sink) for that. This bridge covers
    URL-casting (HLS/DASH/MP4 files and lives), which is what Android's Cast
    menu sends to Chromecasts.
    """

    @staticmethod
    def rtsp_setup_to_media(presentation_url: str, video_formats: str = "") -> dict | None:
        # Some senders use http(s)://*.m3u8/mpd/mp4 as presentation URL and
        # those play directly. Pure rtsp:// does not.
        _ = video_formats  # reserved for future format negotiation
        if presentation_url.startswith(("http://", "https://")):
            return {"url": presentation_url, "streamFormat": guess_format(presentation_url)}
        return None
