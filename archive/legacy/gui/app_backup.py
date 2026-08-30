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

        # =====================================================
        # CONFIGURAÇÃO DO CUSTOMTKINTER
        # =====================================================

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # =====================================================
        # SISTEMAS DA STAR
        # =====================================================

        self.brain = brain
        self.memory = Memory()
        self.avatar = AvatarManager()

        # =====================================================
        # JANELA PRINCIPAL
        # =====================================================

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

        # Permitir redimensionamento
        self.window.resizable(True, True)

        # =====================================================
        # CONTROLE DE ESTADO
        # =====================================================

        self.current_screen = None

        self.is_maximized = False

        self.normal_width = WINDOW_WIDTH
        self.normal_height = WINDOW_HEIGHT

        # =====================================================
        # EVENTOS DO TECLADO
        # =====================================================

        self.window.bind(
            "<F11>",
            self.toggle_maximize
        )

        self.window.bind(
            "<Escape>",
            self.restore_normal_size
        )

        # =====================================================
        # ATUALIZAÇÃO DO MENU QUANDO A JANELA MUDA DE TAMANHO
        # =====================================================

        self.window.bind(
            "<Configure>",
            self.on_window_resize
        )

        self.resize_after_id = None

        # =====================================================
        # INICIAR
        # =====================================================

        self.show_menu()

    # =========================================================
    # MENU
    # =========================================================

    def show_menu(self):

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

        if not MENU_IMAGE_PATH.exists():

            error_label = ctk.CTkLabel(
                self.menu_frame,
                text=(
                    "Imagem do menu não encontrada.\n\n"
                    "Coloque a imagem em:\n\n"
                    f"{MENU_IMAGE_PATH}"
                ),
                font=("Segoe UI", 18)
            )

            error_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center"
            )

            return

        # Carregar imagem original
        self.menu_original_image = Image.open(
            MENU_IMAGE_PATH
        ).convert("RGB")

        # Label responsável pela imagem
        self.menu_label = ctk.CTkLabel(
            self.menu_frame,
            text="",
            fg_color="black"
        )

        self.menu_label.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        # Clique no menu
        self.menu_label.bind(
            "<Button-1>",
            self.menu_click
        )

        # Primeira renderização
        self.update_menu_image()

    # =========================================================
    # REDIMENSIONAMENTO DO MENU
    # =========================================================

    def update_menu_image(self):

        if self.current_screen != "menu":
            return

        if not hasattr(self, "menu_original_image"):
            return

        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        if window_width <= 1 or window_height <= 1:
            return

        original_width, original_height = (
            self.menu_original_image.size
        )

        # =====================================================
        # CALCULAR ESCALA SEM DISTORCER
        # =====================================================

        scale_x = window_width / original_width
        scale_y = window_height / original_height

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

        # =====================================================
        # REDIMENSIONAR
        # =====================================================

        resized_image = self.menu_original_image.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

        self.menu_photo = ImageTk.PhotoImage(
            resized_image
        )

        self.menu_label.configure(
            image=self.menu_photo
        )

        # =====================================================
        # GUARDAR ESCALA ATUAL
        # =====================================================

        self.menu_scale = scale

        self.menu_display_width = new_width
        self.menu_display_height = new_height

        self.menu_offset_x = (
            window_width - new_width
        ) / 2

        self.menu_offset_y = (
            window_height - new_height
        ) / 2

    # =========================================================
    # EVENTO DE REDIMENSIONAMENTO
    # =========================================================

    def on_window_resize(self, event):

        if event.widget != self.window:
            return

        if self.current_screen != "menu":
            return

        # Evitar centenas de atualizações seguidas
        if self.resize_after_id is not None:

            self.window.after_cancel(
                self.resize_after_id
            )

        self.resize_after_id = self.window.after(
            50,
            self.update_menu_image
        )

    # =========================================================
    # CLIQUE NO MENU
    # =========================================================

    def menu_click(self, event):

        if not hasattr(self, "menu_scale"):
            return

        # =====================================================
        # CONVERTER COORDENADAS DA JANELA PARA A IMAGEM
        # =====================================================

        image_x = (
            event.x - self.menu_offset_x
        ) / self.menu_scale

        image_y = (
            event.y - self.menu_offset_y
        ) / self.menu_scale

        # Se clicou fora da imagem
        if image_x < 0:
            return

        if image_y < 0:
            return

        if image_x > 1200:
            return

        if image_y > 896:
            return

        # =====================================================
        # ÁREAS DOS BOTÕES
        #
        # Essas coordenadas são aproximadas.
        # Ajustaremos depois observando a arte.
        # =====================================================

        # INICIAR
        if (
            400 <= image_x <= 800
            and
            550 <= image_y <= 640
        ):

            self.show_chat()

        # CONFIGURAÇÕES
        elif (
            400 <= image_x <= 800
            and
            650 <= image_y <= 735
        ):

            self.show_settings()

        # SAIR
        elif (
            400 <= image_x <= 800
            and
            750 <= image_y <= 835
        ):

            self.window.destroy()

    # =========================================================
    # CONFIGURAÇÕES
    # =========================================================

    def show_settings(self):

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

        # Carregar memória
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

        # Colocar o cursor no campo
        self.entry.focus_set()

    # =========================================================
    # ENVIAR MENSAGEM
    # =========================================================

    def send_message(self):

        message = self.entry.get().strip()

        if not message:
            return

        # Salvar mensagem do usuário
        self.memory.save(
            "Você",
            message
        )

        self.chat.insert(
            "end",
            f"Você: {message}\n"
        )

        # Processar pelo Brain
        response = self.brain.process(
            message
        )

        # Salvar resposta
        self.memory.save(
            "STAR",
            response
        )

        self.chat.insert(
            "end",
            f"STAR: {response}\n\n"
        )

        # Limpar campo
        self.entry.delete(
            0,
            "end"
        )

        self.chat.see(
            "end"
        )

    # =========================================================
    # MAXIMIZAR / RESTAURAR
    # =========================================================

    def toggle_maximize(self, event=None):

        if self.is_maximized:

            self.restore_normal_size()

        else:

            self.maximize_window()

    def maximize_window(self):

        # Salvar tamanho atual antes de maximizar
        self.normal_width = self.window.winfo_width()
        self.normal_height = self.window.winfo_height()

        if self.normal_width <= 1:
            self.normal_width = WINDOW_WIDTH

        if self.normal_height <= 1:
            self.normal_height = WINDOW_HEIGHT

        # Maximizar
        self.window.state("zoomed")

        self.is_maximized = True

    def restore_normal_size(self, event=None):

        if not self.is_maximized:
            return

        self.window.state("normal")

        self.window.geometry(
            f"{self.normal_width}x{self.normal_height}"
        )

        self.is_maximized = False

    # =========================================================
    # LIMPAR TELA
    # =========================================================

    def clear_screen(self):

        for widget in self.window.winfo_children():

            widget.destroy()

        # Limpar referências da imagem
        if hasattr(self, "menu_photo"):
            self.menu_photo = None

    # =========================================================
    # EXECUTAR
    # =========================================================

    def run(self):

        self.window.mainloop()