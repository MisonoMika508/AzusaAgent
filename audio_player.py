import winsound


class AudioPlayer:

    def play(self, audio_path):

        print("正在播放：")
        print(audio_path)

        winsound.PlaySound(
            audio_path,
            winsound.SND_FILENAME
        )