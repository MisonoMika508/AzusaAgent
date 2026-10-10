# -*- coding: utf-8 -*-

import os
import sys
import importlib.util
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

import keyboard

from PIL import Image, ImageTk


# ============================================================
# FFmpeg
# ============================================================

FFMPEG_BIN = r"D:\OTHERS\AI\ffmpeg\bin"

os.environ["PATH"] = (
    FFMPEG_BIN
    + os.pathsep
    + os.environ.get("PATH", "")
)


print(
    "FFmpeg:",
    __import__("shutil").which("ffmpeg")
)


# ============================================================
# 当前目录
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


if BASE_DIR not in sys.path:

    sys.path.insert(
        0,
        BASE_DIR
    )


# ============================================================
# 强制加载当前目录 ollama_client.py
# ============================================================

OLLAMA_CLIENT_PATH = os.path.join(
    BASE_DIR,
    "ollama_client.py"
)


if not os.path.isfile(
    OLLAMA_CLIENT_PATH
):

    raise FileNotFoundError(
        "找不到 ollama_client.py：\n"
        + OLLAMA_CLIENT_PATH
    )


spec = (
    importlib.util
    .spec_from_file_location(
        "ollama_client",
        OLLAMA_CLIENT_PATH
    )
)


ollama_module = (
    importlib.util
    .module_from_spec(spec)
)


spec.loader.exec_module(
    ollama_module
)


OllamaClient = (
    ollama_module.OllamaClient
)


from tts import GPTSoVITS
from audio_player import AudioPlayer


# ============================================================
# 全局设置
# ============================================================

WINDOW_TITLE = "Azusa Agent"

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 500

TOGGLE_HOTKEY = "alt+c"

QUIT_HOTKEY = "alt+q"


# ============================================================
# Azusa Agent UI
# ============================================================

class AgentUI:

    def __init__(
        self,
        root,
        ai,
        tts,
        player,
    ):

        self.root = root

        self.ai = ai

        self.tts = tts

        self.player = player


        # ----------------------------------------------------
        # 状态
        # ----------------------------------------------------

        self.visible = False

        self.processing = False

        self.exiting = False

        self.speech_queue = queue.Queue()
        self.speech_worker = threading.Thread(
            target=self._speech_worker,
            daemon=True,
        )
        self.speech_worker.start()


        # ====================================================
        # 图片引用
        # ====================================================
        #
        # Tkinter 的 PhotoImage 如果没有 Python 引用，
        # 图片可能会自动消失。
        #
        # 所以必须保存起来。
        #

        self.chat_image_refs = []

        self.chat_image_labels = []


        # ====================================================
        # 窗口
        # ====================================================

        self.root.title(
            WINDOW_TITLE
        )


        self.root.geometry(
            "520x360"
        )


        self.root.minsize(
            420,
            260
        )


        self.root.resizable(
            True,
            True
        )


        # ----------------------------------------------------
        # 窗口关闭按钮
        # ----------------------------------------------------

        self.root.protocol(

            "WM_DELETE_WINDOW",

            self.hide_window

        )


        # ====================================================
        # 整体布局
        # ====================================================

        self.root.grid_rowconfigure(

            0,

            weight=1

        )


        self.root.grid_rowconfigure(

            1,

            weight=0

        )


        self.root.grid_columnconfigure(

            0,

            weight=1

        )


        # ====================================================
        # 聊天区域
        # ====================================================

        chat_frame = tk.Frame(

            self.root

        )


        chat_frame.grid(

            row=0,

            column=0,

            sticky="nsew",

            padx=8,

            pady=(8, 4),

        )


        chat_frame.grid_rowconfigure(

            0,

            weight=1

        )


        chat_frame.grid_columnconfigure(

            0,

            weight=1

        )


        self.chat_box = scrolledtext.ScrolledText(

            chat_frame,

            wrap=tk.WORD,

            font=(

                "Microsoft YaHei",

                10,

            ),

            padx=8,

            pady=8,

        )


        self.chat_box.grid(

            row=0,

            column=0,

            sticky="nsew"

        )


        self.chat_box.configure(

            state="disabled"

        )


        # ====================================================
        # 输入区域
        # ====================================================

        input_frame = tk.Frame(

            self.root

        )


        input_frame.grid(

            row=1,

            column=0,

            sticky="ew",

            padx=8,

            pady=(4, 8),

        )


        input_frame.grid_columnconfigure(

            0,

            weight=1

        )


        # ----------------------------------------------------
        # 输入框
        # ----------------------------------------------------

        self.input_box = tk.Entry(

            input_frame,

            font=(

                "Microsoft YaHei",

                11,

            ),

        )


        self.input_box.grid(

            row=0,

            column=0,

            sticky="ew",

            ipady=6,

        )


        # ====================================================
        # 发送按钮
        # ====================================================

        self.send_button = tk.Button(

            input_frame,

            text="发送",

            width=8,

            command=self.submit,

        )


        self.send_button.grid(

            row=0,

            column=1,

            padx=(8, 0),

        )


        # ====================================================
        # Enter 发送
        # ====================================================

        self.input_box.bind(

            "<Return>",

            self.on_enter

        )


        # ====================================================
        # 初始隐藏
        # ====================================================

        self.root.withdraw()


    # ========================================================
    # 显示窗口
    # ========================================================

    def show_window(self):

        if self.exiting:

            return


        self.visible = True


        # ====================================================
        # 计算窗口位置
        # ====================================================

        window_width = 520

        window_height = 360


        screen_width = (
            self.root.winfo_screenwidth()
        )

        screen_height = (
            self.root.winfo_screenheight()
        )


        x = (
            screen_width
            - window_width
        ) // 2


        y = (
            screen_height
            - window_height
        ) // 2


        self.root.geometry(

            f"{window_width}x"
            f"{window_height}+"
            f"{x}+{y}"

        )


        # ====================================================
        # 显示
        # ====================================================

        self.root.deiconify()


        self.root.lift()


        self.root.attributes(

            "-topmost",

            True

        )


        # ====================================================
        # 自动获得输入焦点
        # ====================================================

        self.root.after(

            50,

            self.input_box.focus_force

        )


        # ----------------------------------------------------
        # 短暂置顶
        # ----------------------------------------------------

        self.root.after(

            500,

            lambda: self.root.attributes(

                "-topmost",

                False

            )

        )


    # ========================================================
    # 隐藏窗口
    # ========================================================

    def hide_window(self):

        self.visible = False

        self.root.withdraw()


    # ========================================================
    # Alt+C
    # ========================================================

    def toggle_window(self):

        self.root.after(

            0,

            self._toggle_window_ui

        )


    def _toggle_window_ui(self):

        if self.exiting:

            return


        if self.visible:

            self.hide_window()

        else:

            self.show_window()


    # ========================================================
    # Enter
    # ========================================================

    def on_enter(
        self,
        event=None,
    ):

        self.submit()

        return "break"


    # ========================================================
    # 添加聊天文字
    # ========================================================

    def append_chat(
        self,
        speaker,
        text,
    ):

        self.chat_box.configure(
            state="normal"
        )


        self.chat_box.insert(

            tk.END,

            f"{speaker}：\n"

        )


        self.chat_box.insert(

            tk.END,

            f"{text}\n\n"

        )


        self.chat_box.see(
            tk.END
        )


        self.chat_box.configure(
            state="disabled"
        )


    # ========================================================
    # 添加生成图片
    # ========================================================

    def append_image(
        self,
        image_path,
    ):

        if self.exiting:

            return


        if not image_path:

            return


        image_path = os.path.abspath(
            image_path
        )


        print(
            "[UI] 显示图片：",
            image_path
        )


        if not os.path.isfile(
            image_path
        ):

            print(
                "[UI] 图片不存在：",
                image_path
            )

            self.append_chat(

                "系统",

                "图片文件不存在："
                + image_path

            )

            return


        try:

            # =================================================
            # 打开图片
            # =================================================

            image = Image.open(
                image_path
            )


            # =================================================
            # 缩放
            # =================================================
            #
            # 最大显示尺寸：
            # 420 x 320
            #
            # 不修改原文件。
            #

            max_width = 420

            max_height = 320


            try:

                resample = (
                    Image.Resampling.LANCZOS
                )

            except AttributeError:

                resample = Image.LANCZOS


            image.thumbnail(

                (
                    max_width,
                    max_height
                ),

                resample

            )


            # =================================================
            # 转 Tkinter 图片
            # =================================================

            photo = ImageTk.PhotoImage(
                image
            )


            # =================================================
            # 创建图片 Label
            # =================================================

            image_label = tk.Label(

                self.chat_box,

                image=photo,

                cursor="hand2",

                bd=0,

                relief=tk.FLAT,

            )


            # =================================================
            # 点击图片
            # =================================================

            image_label.bind(

                "<Button-1>",

                lambda event,
                path=image_path:
                self.open_generated_image(path)

            )


            # 鼠标悬停时显示提示

            image_label.bind(

                "<Enter>",

                lambda event:
                image_label.configure(
                    cursor="hand2"
                )

            )


            # =================================================
            # 保存引用
            # =================================================

            self.chat_image_refs.append(
                photo
            )

            self.chat_image_labels.append(
                image_label
            )


            # =================================================
            # 插入聊天框
            # =================================================

            self.chat_box.configure(
                state="normal"
            )


            self.chat_box.insert(

                tk.END,

                "\n"

            )


            self.chat_box.window_create(

                tk.END,

                window=image_label

            )


            self.chat_box.insert(

                tk.END,

                "\n\n"

            )


            self.chat_box.see(
                tk.END
            )


            self.chat_box.configure(
                state="disabled"
            )


            print(
                "[UI] 图片显示成功"
            )


        except Exception as e:

            print(
                "[UI] 图片显示失败：",
                type(e).__name__,
                e
            )


            self.append_chat(

                "系统",

                "图片显示失败："
                f"{type(e).__name__}: {e}"

            )


    # ========================================================
    # 打开生成图片
    # ========================================================

    def open_generated_image(
        self,
        image_path,
    ):

        if not os.path.isfile(
            image_path
        ):

            print(
                "[UI] 找不到图片：",
                image_path
            )

            return


        try:

            print(
                "[UI] 打开图片：",
                image_path
            )


            # Windows 默认程序打开图片

            os.startfile(
                image_path
            )


        except Exception as e:

            print(
                "[UI] 打开图片失败：",
                type(e).__name__,
                e
            )


    # ========================================================
    # 显示 Agent 回复 + 图片
    # ========================================================

    def append_agent_response(
        self,
        answer,
        image_paths,
    ):

        # ====================================================
        # 先显示文字
        # ====================================================

        self.append_chat(

            "Azusa",

            answer

        )


        # ====================================================
        # 再显示图片
        # ====================================================

        if image_paths:

            for image_path in image_paths:

                self.append_image(
                    image_path
                )

    def _speech_worker(self):
        while True:
            text = self.speech_queue.get()

            try:
                audio_path = self.tts.speak(text)
                if audio_path:
                    self.player.play(audio_path)
            except Exception as e:
                print(
                    "[TTS] 中间/最终回复语音处理失败："
                    f"{type(e).__name__}: {e}"
                )
                error_text = f"语音播放失败：{type(e).__name__}: {e}"
                self.root.after(
                    0,
                    lambda message=error_text: self.append_chat(
                        "系统",
                        message,
                    ),
                )
            finally:
                self.speech_queue.task_done()

    def _handle_intermediate_response(self, text):
        self.root.after(
            0,
            lambda message=text: self.append_chat(
                "Azusa",
                message,
            ),
        )
        self.speech_queue.put(text)


    # ========================================================
    # 用户发送消息
    # ========================================================

    def submit(self):

        if self.processing:

            return


        user_text = (
            self.input_box
            .get()
            .strip()
        )


        if not user_text:

            return


        # ====================================================
        # 清空输入框
        # ====================================================

        self.input_box.delete(

            0,

            tk.END

        )


        # ====================================================
        # 显示用户消息
        # ====================================================

        self.append_chat(

            "你",

            user_text

        )


        # ====================================================
        # Agent 后台执行
        # ====================================================

        self.processing = True


        self.send_button.config(
            state="disabled"
        )


        worker = threading.Thread(

            target=self.process_message,

            args=(user_text,),

            daemon=True,

        )


        worker.start()


    # ========================================================
    # Agent 工作线程
    # ========================================================

    def process_message(
        self,
        user_text,
    ):

        try:

            print()

            print(
                "[Agent] 正在处理..."
            )


            # =================================================
            # Agent
            # =================================================

            answer = self.ai.chat(

                user_text,
                on_intermediate=self._handle_intermediate_response,

            )


            # =================================================
            # 获取本次生成的图片
            # =================================================
            #
            # ollama_client.py 中 chat() 每次开始时
            # 都会清空 generated_images。
            #

            generated_images = list(

                getattr(

                    self.ai,

                    "generated_images",

                    []

                )

            )


            print()

            print(
                "Azusa："
            )

            print(
                answer
            )


            if generated_images:

                print()

                print(
                    "[ComfyUI] 本次生成图片："
                )


                for image_path in generated_images:

                    print(
                        "  ",
                        image_path
                    )


            # =================================================
            # UI 显示文字 + 图片
            # =================================================

            self.root.after(

                0,

                lambda
                a=answer,
                imgs=generated_images:

                self.append_agent_response(

                    a,

                    imgs

                )

            )


            self.speech_queue.put(answer)
            self.speech_queue.join()


        except Exception as e:

            print()

            print(
                "=" * 60
            )

            print(
                "发生错误"
            )

            print(
                "=" * 60
            )

            print(
                type(e).__name__
            )

            print(
                e
            )

            print(
                "=" * 60
            )


            error_text = (
                f"发生错误："
                f"{type(e).__name__}: {e}"
            )


            self.root.after(

                0,

                lambda:
                self.append_chat(

                    "系统",

                    error_text

                )

            )


        finally:

            # =================================================
            # 恢复发送按钮
            # =================================================

            self.root.after(

                0,

                self.finish_processing

            )


    # ========================================================
    # Agent 工作完成
    # ========================================================

    def finish_processing(self):

        self.processing = False


        if not self.exiting:

            self.send_button.config(

                state="normal"

            )


            if self.visible:

                self.input_box.focus_force()


    # ========================================================
    # Alt+Q
    # ========================================================

    def quit_program(self):

        self.root.after(

            0,

            self._quit_program_ui

        )


    def _quit_program_ui(self):

        if self.exiting:

            return


        self.exiting = True


        print()

        print(
            "Alt+Q 被按下"
        )

        print(
            "Azusa Agent 正在退出..."
        )


        # ====================================================
        # 停止全局快捷键
        # ====================================================

        try:

            keyboard.unhook_all()

        except Exception:

            pass


        # ====================================================
        # 关闭 Tkinter
        # ====================================================

        try:

            self.root.quit()

        except Exception:

            pass


        try:

            self.root.destroy()

        except Exception:

            pass


        # ====================================================
        # 强制结束 Python 进程
        # ====================================================

        print(
            "Azusa Agent 已退出。"
        )


        os._exit(0)


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)

    print(
        "Azusa Agent"
    )

    print("=" * 60)


    # ========================================================
    # Agent
    # ========================================================

    print()

    print(
        "初始化 Agent..."
    )


    ai = OllamaClient()


    # ========================================================
    # TTS
    # ========================================================

    print()

    print(
        "初始化 GPT-SoVITS..."
    )


    tts = GPTSoVITS()


    # ========================================================
    # Audio
    # ========================================================

    print()

    print(
        "初始化播放器..."
    )


    player = AudioPlayer()


    # ========================================================
    # Tkinter
    # ========================================================

    print()

    print(
        "初始化 Agent 窗口..."
    )


    root = tk.Tk()


    app = AgentUI(

        root,

        ai,

        tts,

        player,

    )


    # ========================================================
    # 注册全局快捷键
    # ========================================================

    print()

    print(
        f"注册快捷键："
        f"{TOGGLE_HOTKEY}"
        f" / "
        f"{QUIT_HOTKEY}"
    )


    keyboard.add_hotkey(

        TOGGLE_HOTKEY,

        app.toggle_window,

    )


    keyboard.add_hotkey(

        QUIT_HOTKEY,

        app.quit_program,

    )


    # ========================================================
    # 启动完成
    # ========================================================

    print()

    print("=" * 60)

    print(
        "Azusa Agent 已启动"
    )

    print("=" * 60)

    print()

    print(
        "Alt+C  → 显示 / 隐藏 Agent"
    )

    print(
        "Alt+Q  → 退出 Agent"
    )

    print()

    print(
        "窗口默认隐藏，Agent 在后台运行。"
    )

    print(
        "显示窗口后，可以直接使用 Win+H 语音输入。"
    )

    print(
        "Enter → 发送"
    )

    print("=" * 60)


    # ========================================================
    # Tkinter 主循环
    # ========================================================

    try:

        root.mainloop()


    except KeyboardInterrupt:

        print()

        print(
            "程序退出"
        )


    finally:

        try:

            keyboard.unhook_all()

        except Exception:

            pass


# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":

    main()