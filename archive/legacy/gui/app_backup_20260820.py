import customtkinter as ctk

from pathlib import Path
from PIL import Image, ImageTk

from config import (
    APP_NAME,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
)

from database.memory import Memory
from core.avatar import AvatarManager


BASE_DIR = Path(__file__).resolve().parent.parent

ICON_PATH = BASE_DIR / "assets" / "icons" / "star.ico"
MENU_IMAGE_PATH = BASE_DIR / "assets" / "images" / "menu.png"


class StarApp:

    def __init__(self, brain):

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.brain = brain
        self.memory = Memory()
        self.avatar = AvatarManager()

        self.window = ctk.CTk()

        self.window.title(APP_NAME)

        if ICON_PATH.exists():
            self.window.iconbitmap(str(ICON_PATH))

        self.window.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.window.minsize(
            MIN_WINDOW_WIDTH,
            MIN_WINDOW_HEIGHT
        )

        self.window.resizable(
            True,
            True
        )

        self.current_screen = None
        self.is_maximized = False

        self.resize_after_id = None
        self.menu_render_after_id = None

        self.menu_original_image = None
        self.menu_photo = None
        self.menu_scale = 1
        self.menu_image_x = 0
        self.menu_image_y = 0

        self.window.bind(
            "<F11>",
            self.toggle_maximize
        )

        self.window.bind(
            "<Escape>",
            self.restore_normal_size
        )

        self.window.bind(
            "<Configure>",
            self.on_window_resize
        )

        self.show_menu()

    # =========================================================
    # MENU
    # =========================================================

    def show_menu(self):

        self.cancel_pending_callbacks()

        self.clear_screen()

        self.current_screen = "menu"

        self.menu_frame = ctk.CTkFrame(
            self.window,
            fg_color="black",
            corner_radius=0
        )

        self.menu_frame.pack(
            fill="both",
            expand=True
        )

        self.menu_canvas = ctk.CTkCanvas(
            self.menu_frame,
            bg="black",
            highlightthickness=0,
            bd=0
        )

        self.menu_canvas.pack(
            fill="both",
            expand=True
        )

        self.menu_canvas.bind(
            "<Button-1>",
            self.menu_click
        )

        if not MENU_IMAGE_PATH.exists():

            self.menu_canvas.create_text(
                WINDOW_WIDTH // 2,
                WINDOW_HEIGHT // 2,
                text=(
                    "Imagem do menu não encontrada.\n\n"
                    f"{MENU_IMAGE_PATH}"
                ),
                fill="white",
                font=("Segoe UI", 18),
                justify="center"
            )

            return

        try:

            self.menu_original_image = Image.open(
                MENU_IMAGE_PATH
            ).convert("RGB")

        except Exception as error:

            self.menu_canvas.create_text(
                WINDOW_WIDTH // 2,
                WINDOW_HEIGHT // 2,
                text=(
                    "Não foi possível carregar a imagem do menu.\n\n"
                    f"{error}"
                ),
                fill="white",
                font=("Segoe UI", 18),
                justify="center"
            )

            return

        self.menu_render_after_id = self.window.after_idle(
            self.update_menu_image
        )

    # =========================================================
    # RENDERIZAR MENU
    # =========================================================

    def update_menu_image(self):

        self.menu_render_after_id = None

        if self.current_screen != "menu":
            return

        if not hasattr(
            self,
            "menu_canvas"
        ):
            return

        if not self.menu_canvas.winfo_exists():
            return

        if self.menu_original_image is None:
            return

        canvas_width = self.menu_canvas.winfo_width()
        canvas_height = self.menu_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:

            self.menu_render_after_id = self.window.after(
                50,
                self.update_menu_image
            )

            return

        original_width, original_height = (
            self.menu_original_image.size
        )

        scale_x = (
            canvas_width / original_width
        )

        scale_y = (
            canvas_height / original_height
        )

        scale = min(
            scale_x,
            scale_y
        )

        new_width = max(
            1,
            int(original_width * scale)
        )

        new_height = max(
            1,
            int(original_height * scale)
        )

        resized_image = self.menu_original_image.resize(
            (
                new_width,
                new_height
            ),
            Image.Resampling.LANCZOS
        )

        self.menu_photo = ImageTk.PhotoImage(
            resized_image
        )

        self.menu_canvas.delete(
            "all"
        )

        self.menu_image_x = (
            canvas_width - new_width
        ) / 2

        self.menu_image_y = (
            canvas_height - new_height
        ) / 2

        self.menu_canvas.create_image(
            self.menu_image_x,
            self.menu_image_y,
            image=self.menu_photo,
            anchor="nw"
        )

        self.menu_scale = scale

        self.menu_display_width = new_width
        self.menu_display_height = new_height

    # =========================================================
    # REDIMENSIONAMENTO DA JANELA
    # =========================================================

    def on_window_resize(self, event):

        if event.widget != self.window:
            return

        if self.current_screen != "menu":
            return

        if self.resize_after_id is not None:

            try:
                self.window.after_cancel(
                    self.resize_after_id
                )
            except Exception:
                pass

            self.resize_after_id = None

        self.resize_after_id = self.window.after(
            30,
            self.update_menu_image
        )

    # =========================================================
    # CLIQUES DO MENU
    # =========================================================

    def menu_click(self, event):

        if not hasattr(
            self,
            "menu_scale"
        ):
            return

        if self.menu_scale <= 0:
            return

        image_x = (
            event.x - self.menu_image_x
        ) / self.menu_scale

        image_y = (
            event.y - self.menu_image_y
        ) / self.menu_scale

        if image_x < 0:
            return

        if image_y < 0:
            return

        if image_x > 1200:
            return

        if image_y > 896:
            return

        # -----------------------------------------------------
        # INICIAR
        # -----------------------------------------------------

        if (
            400 <= image_x <= 800
            and
            540 <= image_y <= 635
        ):

            self.show_chat()
            return

        # -----------------------------------------------------
        # CONFIGURAÇÕES
        # -----------------------------------------------------

        if (
            400 <= image_x <= 800
            and
            640 <= image_y <= 735
        ):

            self.show_settings()
            return

        # -----------------------------------------------------
        # SAIR
        # -----------------------------------------------------

        if (
            400 <= image_x <= 800
            and
            740 <= image_y <= 840
        ):

            self.window.destroy()
            return

    # =========================================================
    # CONFIGURAÇÕES
    # =========================================================

    def show_settings(self):

        self.cancel_pending_callbacks()

        self.clear_screen()

        self.current_screen = "settings"

        frame = ctk.CTkFrame(
            self.window
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=40
        )

        title = ctk.CTkLabel(
            frame,
            text="CONFIGURAÇÕES",
            font=("Segoe UI", 30, "bold")
        )

        title.pack(
            pady=(80, 20)
        )

        text = ctk.CTkLabel(
            frame,
            text=(
                "As configurações da STAR ainda estão\n"
                "em desenvolvimento. ⭐"
            ),
            font=("Segoe UI", 18)
        )

        text.pack(
            pady=20
        )

        back_button = ctk.CTkButton(
            frame,
            text="VOLTAR",
            command=self.show_menu,
            width=200,
            height=45
        )

        back_button.pack(
            pady=30
        )

    # =========================================================
    # CHAT
    # =========================================================

    def show_chat(self):

        self.cancel_pending_callbacks()

        self.clear_screen()

        self.current_screen = "chat"

        # =====================================================
        # TOPO
        # =====================================================

        top = ctk.CTkFrame(
            self.window,
            height=50
        )

        top.pack(
            fill="x"
        )

        title = ctk.CTkLabel(
            top,
            text="STAR",
            font=("Segoe UI", 22, "bold")
        )

        title.pack(
            side="left",
            padx=20,
            pady=10
        )

        status = ctk.CTkLabel(
            top,
            text="Online"
        )

        status.pack(
            side="right",
            padx=20
        )

        menu_button = ctk.CTkButton(
            top,
            text="MENU",
            width=80,
            command=self.show_menu
        )

        menu_button.pack(
            side="right",
            padx=10
        )

        # =====================================================
        # ÁREA PRINCIPAL
        # =====================================================

        main = ctk.CTkFrame(
            self.window
        )

        main.pack(
            fill="both",
            expand=True
        )

        # =====================================================
        # SIDEBAR
        # =====================================================

        sidebar = ctk.CTkFrame(
            main,
            width=220
        )

        sidebar.pack(
            side="left",
            fill="y",
            padx=5,
            pady=5
        )

        ctk.CTkLabel(
            sidebar,
            text="Conversas",
            font=("Segoe UI", 18, "bold")
        ).pack(
            pady=15
        )

        ctk.CTkButton(
            sidebar,
            text="+ Nova Conversa"
        ).pack(
            fill="x",
            padx=10
        )

        # =====================================================
        # AVATAR
        # =====================================================

        avatar_frame = ctk.CTkFrame(
            main,
            width=280
        )

        avatar_frame.pack(
            side="left",
            fill="y",
            padx=5,
            pady=5
        )

        avatar_path = self.avatar.get_image_path()

        if avatar_path.exists():

            avatar_pil = Image.open(
                avatar_path
            )

            self.avatar_image = ctk.CTkImage(
                light_image=avatar_pil,
                dark_image=avatar_pil,
                size=(240, 240)
            )

            self.avatar_label = ctk.CTkLabel(
                avatar_frame,
                text="",
                image=self.avatar_image
            )

        else:

            self.avatar_image = None

            self.avatar_label = ctk.CTkLabel(
                avatar_frame,
                text="Avatar não encontrado"
            )

        self.avatar_label.pack(
            padx=20,
            pady=30
        )

        self.emotion_label = ctk.CTkLabel(
            avatar_frame,
            text="Neutral",
            font=("Segoe UI", 16, "bold")
        )

        self.emotion_label.pack(
            pady=10
        )

        # =====================================================
        # CHAT
        # =====================================================

        self.chat = ctk.CTkTextbox(
            main
        )

        self.chat.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        self.chat.insert(
            "end",
            "STAR iniciada.\n\n"
        )

        for message in self.memory.load():

            self.chat.insert(
                "end",
                f"{message.sender}: {message.content}\n"
            )

        self.chat.insert(
            "end",
            "\n"
        )

        # =====================================================
        # CAMPO DE MENSAGEM
        # =====================================================

        bottom = ctk.CTkFrame(
            self.window,
            height=60
        )

        bottom.pack(
            fill="x"
        )

        self.entry = ctk.CTkEntry(
            bottom,
            placeholder_text="Digite sua mensagem..."
        )

        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10,
            pady=10
        )

        self.entry.bind(
            "<Return>",
            lambda event: self.send_message()
        )

        ctk.CTkButton(
            bottom,
            text="Enviar",
            command=self.send_message
        ).pack(
            side="right",
            padx=10
        )

        self.entry.focus_set()

    # =========================================================
    # ENVIAR MENSAGEM
    # =========================================================

    def send_message(self):

        message = self.entry.get().strip()

        if not message:
            return

        self.memory.save(
            "Você",
            message
        )

        self.chat.insert(
            "end",
            f"Você: {message}\n"
        )

        response = self.brain.process(
            message
        )

        self.memory.save(
            "STAR",
            response
        )

        self.chat.insert(
            "end",
            f"STAR: {response}\n\n"
        )

        self.entry.delete(
            0,
            "end"
        )

        self.chat.see(
            "end"
        )

    # =========================================================
    # MAXIMIZAR
    # =========================================================

    def toggle_maximize(self, event=None):

        if self.is_maximized:

            self.restore_normal_size()

        else:

            self.maximize_window()

    # =========================================================
    # MAXIMIZAR JANELA
    # =========================================================

    def maximize_window(self):

        self.window.state(
            "zoomed"
        )

        self.is_maximized = True

        if self.current_screen == "menu":

            self.schedule_menu_render(
                100
            )

    # =========================================================
    # VOLTAR AO TAMANHO NORMAL
    # =========================================================

    def restore_normal_size(self, event=None):

        self.window.state(
            "normal"
        )

        self.window.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.is_maximized = False

        if self.current_screen == "menu":

            self.schedule_menu_render(
                100
            )

    # =========================================================
    # AGENDAR RENDERIZAÇÃO DO MENU
    # =========================================================

    def schedule_menu_render(self, delay=50):

        if self.current_screen != "menu":
            return

        if self.menu_render_after_id is not None:

            try:
                self.window.after_cancel(
                    self.menu_render_after_id
                )
            except Exception:
                pass

        self.menu_render_after_id = self.window.after(
            delay,
            self.update_menu_image
        )

    # =========================================================
    # CANCELAR CALLBACKS
    # =========================================================

    def cancel_pending_callbacks(self):

        if self.resize_after_id is not None:

            try:
                self.window.after_cancel(
                    self.resize_after_id
                )
            except Exception:
                pass

            self.resize_after_id = None

        if self.menu_render_after_id is not None:

            try:
                self.window.after_cancel(
                    self.menu_render_after_id
                )
            except Exception:
                pass

            self.menu_render_after_id = None

    # =========================================================
    # LIMPAR TELA
    # =========================================================

    def clear_screen(self):

        for widget in self.window.winfo_children():

            widget.destroy()

        self.menu_original_image = None
        self.menu_photo = None

        self.menu_scale = 1
        self.menu_image_x = 0
        self.menu_image_y = 0

    # =========================================================
    # EXECUTAR
    # =========================================================

    def run(self):

        self.window.mainloop()