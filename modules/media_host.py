"""Processo auxiliar do WebView da STAR TV."""
from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import urlparse


ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}


def safe_url(value: str) -> str:
    parsed = urlparse(str(value or ""))
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        return "https://www.youtube.com/"
    return value


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://www.youtube.com/")
    parser.add_argument("--x", type=int)
    parser.add_argument("--y", type=int)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    return parser


def command_loop(window):
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue

        command = message.get("command")
        try:
            if command == "load":
                window.load_url(safe_url(message.get("url", "")))
            elif command == "rect":
                window.move(int(message["x"]), int(message["y"]))
                window.resize(int(message["width"]), int(message["height"]))
            elif command == "fullscreen":
                window.toggle_fullscreen()
            elif command == "play":
                window.evaluate_js(
                    "document.querySelector('video') && document.querySelector('video').play()"
                )
            elif command == "pause":
                window.evaluate_js(
                    "document.querySelector('video') && document.querySelector('video').pause()"
                )
            elif command == "volume":
                level = max(0, min(100, int(message.get("value", 100)))) / 100
                window.evaluate_js(
                    f"if(document.querySelector('video')) document.querySelector('video').volume={level}"
                )
            elif command == "close":
                window.destroy()
                return
        except Exception as exc:
            # O host é isolado: uma operação de mídia não derruba o Core,
            # mas a falha precisa permanecer observável para o controlador.
            print(
                "STAR_MEDIA_ERROR:"
                f"{command or 'unknown'}:"
                f"{type(exc).__name__}:{exc}",
                file=sys.stderr,
                flush=True,
            )
            continue


def main():
    args = build_parser().parse_args()
    try:
        import webview
    except ImportError:
        print(
            "pywebview não instalado. Instale requirements-media.txt.",
            file=sys.stderr,
        )
        raise SystemExit(3)

    kwargs = {
        "url": safe_url(args.url),
        "width": max(320, args.width),
        "height": max(180, args.height),
        "resizable": True,
        "background_color": "#05070a",
        "text_select": False,
    }
    if args.x is not None:
        kwargs["x"] = args.x
    if args.y is not None:
        kwargs["y"] = args.y

    window = webview.create_window("STAR TV", **kwargs)
    webview.start(command_loop, window)


if __name__ == "__main__":
    main()
