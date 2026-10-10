import os
import time
import socket
import subprocess

from gradio_client import Client, file

from config import (
    GPT_SOVITS_URL,
    GPT_SOVITS_BAT,
    GPT_MODEL,
    SOVITS_MODEL,
    REF_AUDIO,
    REF_LANGUAGE,
)


class GPTSoVITS:
    def _is_webui_running(self):

        try:

            with socket.create_connection(
                ("127.0.0.1", 9872),
                timeout=1
            ):

                return True

        except OSError:

            return False


    def _start_webui(self):

        if not os.path.isfile(
            GPT_SOVITS_BAT
        ):

            raise FileNotFoundError(
                "找不到 GPT-SoVITS 启动文件：\n"
                + GPT_SOVITS_BAT
            )


        # go-webui.bat 所在目录
        working_dir = os.path.dirname(
            GPT_SOVITS_BAT
        )


        subprocess.Popen(

            [
                "cmd.exe",
                "/c",
                GPT_SOVITS_BAT
            ],

            cwd=working_dir,

            creationflags=subprocess.CREATE_NEW_CONSOLE

        )


    def _wait_for_webui(self, timeout=120):

        start_time = time.time()


        while (
            time.time() - start_time
            < timeout
        ):

            if self._is_webui_running():

                return True


            time.sleep(2)


        return False

    def __init__(self):

        print("连接 GPT-SoVITS...")

        # ========================================================
        # 检查 GPT-SoVITS WebUI 是否已经启动
        # ========================================================

        if not self._is_webui_running():

            print("GPT-SoVITS WebUI 未启动")
            print("正在自动启动 GPT-SoVITS...")

            self._start_webui()

            print("等待 GPT-SoVITS WebUI 启动...")

            if not self._wait_for_webui():

                raise RuntimeError(
                    "GPT-SoVITS WebUI 启动失败，"
                    "9872 端口没有响应。"
                )

        else:

            print("检测到 GPT-SoVITS WebUI 已经运行")


        # ========================================================
        # 连接 WebUI
        # ========================================================

        self.client = Client(
            GPT_SOVITS_URL
        )

        print("GPT-SoVITS 连接成功")


        # ========================================================
        # 自动切换 GPT 权重
        # ========================================================

        print("正在切换 GPT 权重...")

        self.client.predict(
            GPT_MODEL,
            api_name="/change_gpt_weights"
        )

        print(
            "GPT 权重："
            + GPT_MODEL
        )


        # ========================================================
        # 自动切换 SoVITS 权重
        # ========================================================

        print("正在切换 SoVITS 权重...")

        self.client.predict(
            SOVITS_MODEL,
            api_name="/change_sovits_weights"
        )

        print(
            "SoVITS 权重："
            + SOVITS_MODEL
        )


        print("GPT-SoVITS 初始化完成")

        print("GPT-SoVITS 权重切换完成")

    def speak(self, text):

        result = self.client.predict(

            ref_wav_path=file(
                REF_AUDIO
            ),

            # 参考音频文本不知道时可以留空
            prompt_text="",

            prompt_language=REF_LANGUAGE,

            text=text,

            # Qwen输出目前按照中文处理
            text_language="中文",

            how_to_cut="不切",

            top_k=15,

            top_p=1,

            temperature=1,

            ref_free=False,

            speed=1,

            if_freeze=False,

            inp_refs=None,

            sample_steps="32",

            if_sr=False,

            pause_second=0.3,

            api_name="/get_tts_wav"
        )

        return result