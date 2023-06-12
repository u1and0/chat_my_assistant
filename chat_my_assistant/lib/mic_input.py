#!/usr/bin/env python3
"""
Pyaudioをインストールする前に、以下のコマンドを実行して必要な依存関係をインストールする必要があります。

```bash
sudo apt-get install python3-dev portaudio19-dev libffi-dev libssl-dev
```

上記のコマンドを実行した後、以下のコマンドでPyaudio, SpeechRecognition をインストールしてください。

```
pip install pyaudio SpeechRecognition
```

"""
import asyncio
import speech_recognition as sr


async def async_mic_input(language="ja-JP") -> str:
    """
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(
            f"Could not request results from Google Speech Recognition service;{e}"
        )
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        # listen for audio and convert it to text
        loop = asyncio.get_running_loop()
        while True:
            try:
                audio = recognizer.listen(source)
                text = await loop.run_in_executor(None,
                                                  recognizer.recognize_google,
                                                  audio, None, language)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                await asyncio.sleep(1)
                continue
            except sr.RequestError as e:
                print(
                    f"Could not request results from Google Speech Recognition service;{e}"
                )
                await asyncio.sleep(1)
                continue
            if text.strip():
                break
            # text = recognizer.recognize_google(audio, language=language)
            # yield data
        print(text)
        return text
