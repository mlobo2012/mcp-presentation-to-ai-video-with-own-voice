#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Local Chatterbox TTS runner.")
    parser.add_argument("--text", default="")
    parser.add_argument("--voice", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--accent", default=None)
    parser.add_argument("--model", default=os.environ.get("CHATTERBOX_TTS_MODEL"))
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def fail(message: str) -> None:
    raise RuntimeError(message)


def import_runtime():
    missing = []
    modules = {}
    for name in ["torch", "torchaudio"]:
        try:
            modules[name] = __import__(name)
        except Exception:
            missing.append(name)
    try:
        import chatterbox.tts as chatterbox_tts_mod
    except Exception:
        chatterbox_tts_mod = None
        missing.append("chatterbox")
    if missing:
        fail(
            "Missing Chatterbox runtime packages in the selected Python environment: "
            + ", ".join(sorted(set(missing)))
        )
    if getattr(chatterbox_tts_mod.perth, "PerthImplicitWatermarker", None) is None:
        chatterbox_tts_mod.perth.PerthImplicitWatermarker = chatterbox_tts_mod.perth.DummyWatermarker
    modules["ChatterboxTTS"] = chatterbox_tts_mod.ChatterboxTTS
    modules["watermarker"] = chatterbox_tts_mod.perth.PerthImplicitWatermarker.__name__
    return modules


def select_device(torch_mod):
    if getattr(torch_mod.backends, "mps", None) and torch_mod.backends.mps.is_available():
        return "mps"
    if torch_mod.cuda.is_available():
        return "cuda"
    return "cpu"


def preflight(args):
    modules = import_runtime()
    if args.voice and not os.path.exists(args.voice):
        fail(f"Voice sample not found: {args.voice}")
    payload = {
        "provider": "chatterbox",
        "python": sys.executable,
        "device": select_device(modules["torch"]),
        "voice_sample": args.voice or None,
        "model": args.model,
        "watermarker": modules["watermarker"],
    }
    print(json.dumps(payload))


def synthesize(args):
    if not args.output:
        fail("Chatterbox runtime requires --output")
    if not args.text.strip():
        fail("Chatterbox runtime requires --text")
    if not args.voice:
        fail("Chatterbox runtime requires --voice")
    if not os.path.exists(args.voice):
        fail(f"Voice sample not found: {args.voice}")

    modules = import_runtime()
    torch_mod = modules["torch"]
    torchaudio_mod = modules["torchaudio"]
    ChatterboxTTS = modules["ChatterboxTTS"]
    device = select_device(torch_mod)

    try:
        if args.model:
            if not os.path.exists(args.model):
                fail(f"Chatterbox local model path not found: {args.model}")
            model = ChatterboxTTS.from_local(args.model, device=device)
        else:
            model = ChatterboxTTS.from_pretrained(device=device)
    except Exception as exc:
        fail(f"Unable to load Chatterbox model: {exc}")

    prompt_text = args.text.strip()
    if args.accent:
        prompt_text = f"{prompt_text}\n\nAccent guidance: {args.accent}."

    try:
        wav = model.generate(prompt_text, audio_prompt_path=args.voice)
    except TypeError:
        try:
            wav = model.generate(text=prompt_text, audio_prompt_path=args.voice)
        except Exception as exc:
            fail(f"Chatterbox generation failed: {exc}")
    except Exception as exc:
        fail(f"Chatterbox generation failed: {exc}")

    if hasattr(wav, "detach"):
        wav = wav.detach().cpu()
    if getattr(wav, "ndim", 1) == 1:
        wav = wav.unsqueeze(0)

    sample_rate = getattr(model, "sr", 24000)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    torchaudio_mod.save(args.output, wav, sample_rate)


def main():
    args = parse_args()
    try:
        if args.check_only:
            preflight(args)
            return 0
        synthesize(args)
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
