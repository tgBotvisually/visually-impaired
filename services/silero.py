import torch
import soundfile as sf
from torch import device


class Silero:
    def __init__(self):
        self.device = torch.device('cpu')
        self._load_models()

    def _load_models(self):
        self.tts_model, _ = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_tts',
            language='ru',
            speaker='v3_1_ru'
        )
        self.tts_model.to(self.device)

        self.stt_model, self.stt_decoder, self.stt_utils = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_stt',
            language='en',
            device=self.device
        )
        self.stt_model.to(self.device)

    def text_to_speech(self, text: str, speaker: str = 'aidar',
                       sample_rate: int = 48000, output_file: str = 'output.wav'):
        torch.set_num_threads(4)

        audio = self.tts_model.apply_tts(
            text=text,
            speaker=speaker,
            sample_rate=sample_rate
        )

        sf.write(output_file, audio, sample_rate)

        return output_file


silero = Silero()
