import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog # Importar filedialog
import threading
import requests
import os
import json
from datetime import datetime

# Importações para Matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Configurações iniciais do CustomTkinter
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "dark-blue", "green"

BASE_API_URL = 'http://127.0.0.1:5000'

API_LOGIN_URL = f'{BASE_API_URL}/api/login'
API_STATES_URL = f'{BASE_API_URL}/api/estados'
API_CITIES_URL = f'{BASE_API_URL}/api/municipios'
API_CONSULTA_URL = f'{BASE_API_URL}/api/consulta_dados'
API_IMPORT_URL = f'{BASE_API_URL}/api/importar_dataset'
API_UPDATE_URL = f'{BASE_API_URL}/api/atualizar_dados'
API_DELETE_URL = f'{BASE_API_URL}/api/limpar_base'
API_VISUALIZACAO_URL = f'{BASE_API_URL}/api/covid_data_for_plot'


class LoginWindow(ctk.CTkToplevel):
    """
    Janela de login para a aplicação ALERTA-19.
    Permite ao usuário inserir credenciais e selecionar um cargo.
    """
    def __init__(self, app_instance):
        # O super() de um Toplevel precisa saber quem é a janela "mãe"
        super().__init__(app_instance)
        self.app_instance = app_instance # Referência para a instância principal do App

        self.title("ALERTA-19: Login")
        self.geometry("350x300")
        self.resizable(False, False) # Impede redimensionamento

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)

        # Título
        self.label_title = ctk.CTkLabel(self, text="Login ALERTA-19", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.grid(row=0, column=0, pady=20)

        # Campo de Usuário
        self.entry_username = ctk.CTkEntry(self, placeholder_text="Usuário", width=200)
        self.entry_username.grid(row=1, column=0, pady=5)

        # Campo de Senha
        self.entry_password = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=200)
        self.entry_password.grid(row=2, column=0, pady=5)

        # Seleção de Cargo
        self.optionmenu_role = ctk.CTkOptionMenu(self, values=["Administrador", "Civil"])
        self.optionmenu_role.set("Civil") # Padrão
        self.optionmenu_role.grid(row=3, column=0, pady=5)

        # Botão de Login
        self.button_login = ctk.CTkButton(self, text="Entrar", command=self.attempt_login)
        self.button_login.grid(row=4, column=0, pady=10)

        # Feedback Label
        self.label_feedback = ctk.CTkLabel(self, text="", text_color="red")
        self.label_feedback.grid(row=5, column=0, pady=5)

    def attempt_login(self):
        """
        Tenta realizar o login enviando as credenciais para o backend.
        """
        username = self.entry_username.get()
        password = self.entry_password.get()
        role_selection = self.optionmenu_role.get()

        self.label_feedback.configure(text="Autenticando...", text_color="orange")
        threading.Thread(target=self._send_login_request_async,
                         args=(username, password, role_selection)).start()

    def _send_login_request_async(self, username, password, role_selection):
        """
        Envia a requisição de login para o backend de forma assíncrona.
        """
        try:
            response = requests.post(API_LOGIN_URL, json={
                "username": username,
                "password": password
            })
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                returned_role = data.get("role")
                if returned_role == role_selection: # Verifica se o cargo retornado corresponde ao selecionado
                    self.after(0, lambda: self.label_feedback.configure(text="Login realizado com sucesso!", text_color="green"))
                    self.after(500, lambda: self._login_successful(returned_role)) # Pequeno delay para mostrar a mensagem
                else:
                    self.after(0, lambda: self.label_feedback.configure(text=f"Acesso negado para o cargo '{role_selection}'. Cargo correto: {returned_role}.", text_color="red"))
            else:
                self.after(0, lambda: self.label_feedback.configure(text=data.get("message", "Credenciais inválidas."), text_color="red"))
        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self.label_feedback.configure(text="Erro de conexão com o servidor.", text_color="red"))
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.after(0, lambda: self.label_feedback.configure(text="Usuário ou senha incorretos.", text_color="red"))
            else:
                self.after(0, lambda: self.label_feedback.configure(text=f"Erro no servidor: {e}", text_color="red"))
        except json.JSONDecodeError:
            self.after(0, lambda: self.label_feedback.configure(text="Resposta inválida do servidor.", text_color="red"))
        except Exception as e:
            self.after(0, lambda: self.label_feedback.configure(text=f"Erro inesperado: {e}", text_color="red"))

    def _login_successful(self, role):
        """
        Função chamada após o login bem-sucedido.
        Fecha a janela de login e inicia a aplicação principal.
        """
        self.app_instance.user_role = role
        self.destroy() # Fecha a janela de login
        self.app_instance.show_main_app() # Inicia a interface principal


class App(ctk.CTk):
    """
    Classe principal da aplicação ALERTA-19, responsável por gerenciar a interface gráfica
    e a interação com o backend Flask.
    """
    def __init__(self):
        super().__init__()

        # Inicialmente, a janela principal não é exibida
        self.withdraw() # Oculta a janela principal até o login

        # Variáveis de estado da aplicação
        self.current_page = 1
        self.records_per_page = 20
        self.total_records = 0
        self.total_pages = 1
        self.current_state_selection = ""
        self.states = ["Carregando..."]
        self.cities = ["Carregando..."]
        self.records = [] # Armazena os dados da tabela
        self.plot_data = {} # Armazena os dados para o gráfico
        self.user_role = None # Será definido após o login

        # Variáveis para a interface de importação
        self.file_path_entry = None # ctk.CTkEntry para exibir o caminho do arquivo
        self.selected_file_path = "" # Armazena o caminho do arquivo selecionado

     # Inicia a janela de login
    def iniciar_fluxo_de_login(self):
        """
        Este método cria a janela de login e espera ela ser fechada.
        Ele só funciona porque será chamado DEPOIS do mainloop começar.
        """
        janela_login = LoginWindow(self)
        self.wait_window(janela_login) # Espera o login ser feito

        # Após o login, verifica se o usuário foi definido
        if self.user_role:
            # Se o login foi bem-sucedido, mostramos o app principal
            self.show_main_app()
        else:
            # Se o login foi cancelado/falhou, fechamos a aplicação
            self.destroy()

    def show_main_app(self):
        """
        Configura e exibe a janela principal da aplicação após o login.
        """
        self.deiconify() # Mostra a janela principal

        self.title("ALERTA-19: Consulta e Gerenciamento de Dados da COVID-19 no Brasil")
        self.geometry("1200x800")
        self.minsize(900, 600) # Define um tamanho mínimo para a janela
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Componentes da UI
        self.create_widgets()

        # Carregar dados iniciais (estados)
        self.load_states()

        # Aplicar restrições de acesso após o login
        self.apply_access_restrictions()

    def create_widgets(self):
        """
        Cria e posiciona todos os widgets da interface gráfica.
        """
        # Cabeçalho da aplicação
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.app_title = ctk.CTkLabel(self.header_frame, text="ALERTA-19", font=ctk.CTkFont(size=24, weight="bold"))
        self.app_title.grid(row=0, column=0, padx=20, pady=10)

        # Barra de Navegação (nav)
        self.navigation_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.navigation_frame.grid(row=1, column=0, sticky="nswe")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.nav_button_consulta = ctk.CTkButton(self.navigation_frame, text="Consulta de Dados",
                                                  command=self.show_consulta_section, corner_radius=8)
        self.nav_button_consulta.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.nav_button_gerenciamento = ctk.CTkButton(self.navigation_frame, text="Gerenciamento de Dataset",
                                                       command=self.show_gerenciamento_section, corner_radius=8)
        self.nav_button_gerenciamento.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Seções principais
        self.consulta_frame = ctk.CTkFrame(self, corner_radius=8)
        self.gerenciamento_frame = ctk.CTkFrame(self, corner_radius=8)

        self.create_consulta_section(self.consulta_frame)
        self.create_gerenciamento_section(self.gerenciamento_frame)

        # Exibir a seção de consulta por padrão
        self.show_consulta_section()

    def create_consulta_section(self, parent_frame):
        """
        Cria os widgets para a seção de 'Consulta de Dados'.
        """
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(4, weight=1) # Row for the scrollable frame for table and plot

        # Formulário de filtros
        filter_form_frame = ctk.CTkFrame(parent_frame, corner_radius=8)
        filter_form_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        filter_form_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Data Inicial
        ctk.CTkLabel(filter_form_frame, text="Data Inicial:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_data_inicial = ctk.CTkEntry(filter_form_frame, placeholder_text="AAAA-MM-DD")
        self.entry_data_inicial.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Data Final
        ctk.CTkLabel(filter_form_frame, text="Data Final:").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.entry_data_final = ctk.CTkEntry(filter_form_frame, placeholder_text="AAAA-MM-DD")
        self.entry_data_final.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Estado
        ctk.CTkLabel(filter_form_frame, text="Estado:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.optionmenu_estado = ctk.CTkOptionMenu(filter_form_frame, values=self.states,
                                                   command=self.on_state_selected)
        self.optionmenu_estado.grid(row=1, column=2, padx=10, pady=5, sticky="ew")

        # Município
        ctk.CTkLabel(filter_form_frame, text="Município:").grid(row=0, column=3, padx=10, pady=5, sticky="w")
        self.optionmenu_municipio = ctk.CTkOptionMenu(filter_form_frame, values=self.cities)
        self.optionmenu_municipio.grid(row=1, column=3, padx=10, pady=5, sticky="ew")

        # Tipos de Gráfico
        ctk.CTkLabel(filter_form_frame, text="Tipo de Gráfico:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.optionmenu_chart_type = ctk.CTkOptionMenu(filter_form_frame, values=["Casos Diários vs. Óbitos Diários", "Casos Acumulados vs. Óbitos Acumulados"])
        self.optionmenu_chart_type.set("Casos Diários vs. Óbitos Diários")
        self.optionmenu_chart_type.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        # Seleção de Agregação
        ctk.CTkLabel(filter_form_frame, text="Agregação:").grid(row=3, column=1, padx=10, pady=5, sticky="w")
        self.optionmenu_aggregation = ctk.CTkOptionMenu(filter_form_frame, values=["Nenhum", "Estado", "Cidade"])
        self.optionmenu_aggregation.set("Nenhum") # Padrão
        self.optionmenu_aggregation.grid(row=4, column=1, padx=10, pady=5, sticky="ew")


        # Botão Consultar
        self.button_consultar = ctk.CTkButton(filter_form_frame, text="Consultar Dados", command=self.perform_consulta, corner_radius=8)
        self.button_consultar.grid(row=2, column=0, columnspan=2, padx=10, pady=15, sticky="ew")

        # Botão Visualizar Gráfico
        self.button_visualizar_grafico = ctk.CTkButton(filter_form_frame, text="Visualizar Gráfico", command=self.perform_plot_visualization, corner_radius=8)
        self.button_visualizar_grafico.grid(row=2, column=2, columnspan=2, padx=10, pady=15, sticky="ew")


        # Feedback visual para o usuário
        self.consulta_feedback_label = ctk.CTkLabel(parent_frame, text="", text_color="orange")
        self.consulta_feedback_label.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        # Frame para a tabela e o gráfico
        self.results_display_frame = ctk.CTkFrame(parent_frame, corner_radius=8)
        self.results_display_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.results_display_frame.grid_columnconfigure(0, weight=1)
        self.results_display_frame.grid_rowconfigure(0, weight=1)

        # Área da tabela de resultados (inicialmente visível)
        self.table_scroll_frame = ctk.CTkScrollableFrame(self.results_display_frame, corner_radius=8)
        self.table_scroll_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.table_scroll_frame.grid_columnconfigure(0, weight=1)

        # Placeholder para a tabela (usaremos CTkLabel e CTkEntry para simular)
        self.table_headers = ["Data", "Estado", "Município", "Casos Confirmados", "Óbitos", "Novos Casos", "Novos Óbitos"]
        self.table_widgets = [] # Para armazenar os widgets da tabela

        # Área do gráfico (inicialmente oculta)
        self.plot_frame = ctk.CTkFrame(self.results_display_frame, corner_radius=8)
        self.plot_canvas = None # Para armazenar o canvas do Matplotlib
        self.toolbar = None # Para armazenar a barra de ferramentas do Matplotlib

        # Paginação
        pagination_frame = ctk.CTkFrame(parent_frame, corner_radius=8)
        pagination_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        pagination_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.button_anterior = ctk.CTkButton(pagination_frame, text="Anterior", command=self.previous_page, corner_radius=8)
        self.button_anterior.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.label_pagina_info = ctk.CTkLabel(pagination_frame, text="Página 1 de 1")
        self.label_pagina_info.grid(row=0, column=1, padx=10, pady=5)

        self.button_proximo = ctk.CTkButton(pagination_frame, text="Próximo", command=self.next_page, corner_radius=8)
        self.button_proximo.grid(row=0, column=2, padx=10, pady=5, sticky="e")

    def create_gerenciamento_section(self, parent_frame):
        """
        Cria os widgets para a seção de 'Gerenciamento de Dataset'.
        """
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(4, weight=1)

        management_buttons_frame = ctk.CTkFrame(parent_frame, corner_radius=8)
        management_buttons_frame.grid(row=0, column=0, padx=20, pady=50, sticky="nsew")
        management_buttons_frame.grid_columnconfigure(0, weight=1)

        # Campo para exibir o caminho do arquivo selecionado
        self.file_path_label = ctk.CTkLabel(management_buttons_frame, text="Nenhum arquivo selecionado.")
        self.file_path_label.grid(row=0, column=0, padx=20, pady=5, sticky="ew")

        self.button_importar = ctk.CTkButton(management_buttons_frame, text="Importar Novo Dataset",
                                              command=self.import_dataset, corner_radius=8)
        self.button_importar.grid(row=1, column=0, padx=20, pady=15, sticky="ew")

        self.button_atualizar = ctk.CTkButton(management_buttons_frame, text="Atualizar Dados Existentes",
                                               command=self.update_dataset, corner_radius=8)
        self.button_atualizar.grid(row=2, column=0, padx=20, pady=15, sticky="ew")

        self.button_limpar = ctk.CTkButton(management_buttons_frame, text="Limpar Base de Dados",
                                            command=self.clear_dataset, corner_radius=8, fg_color="red")
        self.button_limpar.grid(row=3, column=0, padx=20, pady=15, sticky="ew")

        # Feedback visual para o usuário
        self.gerenciamento_feedback_label = ctk.CTkLabel(parent_frame, text="", text_color="orange")
        self.gerenciamento_feedback_label.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

    def apply_access_restrictions(self):
        """
        Aplica restrições de acesso com base no cargo do usuário.
        """
        if self.user_role == "Civil":
            # Desabilitar ou ocultar botões de gerenciamento para usuários "Civil"
            self.nav_button_gerenciamento.configure(state="disabled")
            self.button_importar.configure(state="disabled")
            self.button_atualizar.configure(state="disabled")
            self.button_limpar.configure(state="disabled")
            self.file_path_label.configure(text="Funcionalidades de gerenciamento restritas ao Administrador.", text_color="red")
        else: # Administrador
            self.nav_button_gerenciamento.configure(state="normal")
            self.button_importar.configure(state="normal")
            self.button_atualizar.configure(state="normal")
            self.button_limpar.configure(state="normal")
            self.file_path_label.configure(text="Nenhum arquivo selecionado.")


    def show_consulta_section(self):
        """Exibe a seção de consulta de dados e oculta as outras."""
        self.consulta_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.gerenciamento_frame.grid_forget()
        # Garante que a tabela esteja visível por padrão ao voltar para a seção de consulta
        self.show_table_view()

    def show_gerenciamento_section(self):
        """Exibe a seção de gerenciamento de dataset e oculta as outras."""
        self.gerenciamento_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.consulta_frame.grid_forget()

    def show_table_view(self):
        """Exibe a tabela de resultados e oculta o gráfico."""
        self.plot_frame.grid_forget()
        if self.plot_canvas:
            self.plot_canvas.get_tk_widget().destroy()
            self.plot_canvas = None
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None
        self.table_scroll_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")


    def show_plot_view(self):
        """Exibe o gráfico e oculta a tabela de resultados."""
        self.table_scroll_frame.grid_forget()
        self.plot_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.plot_frame.grid_columnconfigure(0, weight=1)
        self.plot_frame.grid_rowconfigure(0, weight=1)

    def load_states(self):
        """
        Carrega a lista de estados do backend de forma assíncrona.
        """
        self.optionmenu_estado.set("Carregando Estados...")
        self.states = ["Carregando..."] # Reset states
        self.optionmenu_municipio.set("Selecione um Estado")
        self.cities = ["Carregando..."] # Reset cities
        threading.Thread(target=self._fetch_states_async).start()

    def _fetch_states_async(self):
        """
        Função assíncrona para buscar estados.
        """
        try:
            response = requests.get(API_STATES_URL)
            response.raise_for_status()
            data = response.json()
            if "states" in data and data["states"]:
                self.states = [""] + sorted(data["states"]) # Adiciona opção vazia
            else:
                self.states = ["Nenhum estado encontrado"]
                print("DEBUG: Nenhuma lista de estados na resposta.")

        except requests.exceptions.ConnectionError:
            self.states = ["Erro de Conexão"]
            print(f"ERRO: Não foi possível conectar ao backend em {API_STATES_URL}")
        except requests.exceptions.Timeout:
            self.states = ["Tempo Esgotado"]
            print("ERRO: Requisição de estados excedeu o tempo limite.")
        except requests.exceptions.RequestException as e:
            self.states = ["Erro ao Carregar"]
            print(f"ERRO ao carregar estados: {e}")
        except json.JSONDecodeError:
            self.states = ["Erro no JSON"]
            print("ERRO: Resposta não é um JSON válido ao carregar estados.")
        finally:
            self.after(0, self._update_states_ui) # Atualiza a UI na thread principal

    def _update_states_ui(self):
        """
        Atualiza o OptionMenu de estados na UI.
        """
        self.optionmenu_estado.configure(values=self.states)
        if self.states and self.states[0] not in ["Carregando...", "Erro de Conexão", "Tempo Esgotado", "Erro ao Carregar", "Erro no JSON", "Nenhum estado encontrado"]:
            self.optionmenu_estado.set(self.states[0])
            self.on_state_selected(self.states[0]) # Carrega municípios para o primeiro estado
        else:
            self.optionmenu_estado.set(self.states[0]) # Exibe a mensagem de erro/carregamento
            self.optionmenu_municipio.configure(values=["Selecione um Estado"])
            self.optionmenu_municipio.set("Selecione um Estado")


    def on_state_selected(self, state_uf):
        """
        Chamado quando um estado é selecionado. Carrega os municípios correspondentes.
        """
        self.current_state_selection = state_uf
        self.optionmenu_municipio.set("Carregando Municípios...")
        self.cities = ["Carregando..."] # Reset cities
        if state_uf: # Só busca municípios se um estado válido for selecionado
            threading.Thread(target=self._fetch_cities_async, args=(state_uf,)).start()
        else: # Se o estado for vazio (seleção "Nenhum")
            self.cities = [""] # Opção vazia para municípios
            self.after(0, self._update_cities_ui)


    def _fetch_cities_async(self, state_uf):
        """
        Função assíncrona para buscar municípios de um estado.
        """
        try:
            response = requests.get(API_CITIES_URL, params={"estado": state_uf})
            response.raise_for_status()
            data = response.json()
            if "cities" in data and data["cities"]:
                self.cities = [""] + sorted(data["cities"]) # Adiciona opção vazia
            else:
                self.cities = ["Nenhum município encontrado"]
                print(f"DEBUG: Nenhuma lista de municípios para {state_uf} na resposta.")

        except requests.exceptions.ConnectionError:
            self.cities = ["Erro de Conexão"]
            print(f"ERRO: Não foi possível conectar ao backend em {API_CITIES_URL}")
        except requests.exceptions.Timeout:
            self.cities = ["Tempo Esgotado"]
            print("ERRO: Requisição de municípios excedeu o tempo limite.")
        except requests.exceptions.RequestException as e:
            self.cities = ["Erro ao Carregar"]
            print(f"ERRO ao carregar municípios: {e}")
        except json.JSONDecodeError:
            self.cities = ["Erro no JSON"]
            print("ERRO: Resposta não é um JSON válido ao carregar municípios.")
        finally:
            self.after(0, self._update_cities_ui) # Atualiza a UI na thread principal

    def _update_cities_ui(self):
        """
        Atualiza o OptionMenu de municípios na UI.
        """
        self.optionmenu_municipio.configure(values=self.cities)
        if self.cities and self.cities[0] not in ["Carregando...", "Erro de Conexão", "Tempo Esgotado", "Erro ao Carregar", "Erro no JSON", "Nenhum município encontrado", "Selecione um Estado"]:
            self.optionmenu_municipio.set(self.cities[0])
        else:
            self.optionmenu_municipio.set(self.cities[0]) # Exibe a mensagem de erro/carregamento

    def get_filter_params(self):
        """
        Coleta os valores dos filtros do formulário.
        """
        data_inicial = self.entry_data_inicial.get()
        data_final = self.entry_data_final.get()
        estado = self.optionmenu_estado.get()
        municipio = self.optionmenu_municipio.get()
        chart_type = self.optionmenu_chart_type.get()
        aggregation = self.optionmenu_aggregation.get()

        # Validação básica de datas (formato AAAA-MM-DD)
        if data_inicial and not self._is_valid_date(data_inicial):
            self.after(0, lambda: self.consulta_feedback_label.configure(text="Formato de Data Inicial inválido. Use AAAA-MM-DD.", text_color="red"))
            return None
        if data_final and not self._is_valid_date(data_final):
            self.after(0, lambda: self.consulta_feedback_label.configure(text="Formato de Data Final inválido. Use AAAA-MM-DD.", text_color="red"))
            return None

        params = {
            "data_inicial": data_inicial,
            "data_final": data_final,
            "estado": estado if estado not in ["Carregando...", "Erro de Conexão", "Tempo Esgotado", "Erro ao Carregar", "Erro no JSON", "Nenhum estado encontrado", ""] else "",
            "municipio": municipio if municipio not in ["Carregando...", "Erro de Conexão", "Tempo Esgotado", "Erro ao Carregar", "Erro no JSON", "Nenhum município encontrado", "Selecione um Estado", ""] else "",
            "chart_type": chart_type,
            "aggregation": aggregation
        }
        return params

    def perform_consulta(self):
        """
        Captura os filtros e envia a requisição de consulta para o backend para a tabela.
        """
        params = self.get_filter_params()
        if params is None:
            return

        params["page"] = self.current_page
        params["per_page"] = self.records_per_page

        self.consulta_feedback_label.configure(text="Carregando dados da tabela...", text_color="orange")
        threading.Thread(target=self._fetch_covid_data_async, args=(params,)).start()

    def perform_plot_visualization(self):
        """
        Captura os filtros e envia a requisição para o backend para gerar o gráfico.
        """
        params = self.get_filter_params()
        if params is None:
            return

        self.consulta_feedback_label.configure(text="Gerando gráfico...", text_color="orange")
        threading.Thread(target=self._fetch_plot_data_async, args=(params,)).start()


    def _is_valid_date(self, date_str):
        """Verifica se a string da data está no formato AAAA-MM-DD."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _fetch_covid_data_async(self, params):
        """
        Função assíncrona para buscar dados da COVID-19 para a tabela.
        """
        try:
            response = requests.get(API_CONSULTA_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if "data" in data and "total_records" in data:
                self.records = data["data"]
                self.total_records = data["total_records"]
                self.total_pages = (self.total_records + self.records_per_page - 1) // self.records_per_page
                self.after(0, self._render_table)
                self.after(0, lambda: self.consulta_feedback_label.configure(text="Consulta de tabela concluída.", text_color="green"))
                self.after(0, self.show_table_view) # Garante que a tabela é exibida
            else:
                self.records = []
                self.total_records = 0
                self.total_pages = 1
                self.after(0, self._render_table)
                self.after(0, lambda: self.consulta_feedback_label.configure(text="Nenhum dado encontrado para a tabela.", text_color="red"))
                self.after(0, self.show_table_view) # Garante que a tabela é exibida
                print("DEBUG: Estrutura de resposta inesperada para dados da COVID-19 (tabela).")

        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self.consulta_feedback_label.configure(text="Erro de Conexão com o backend.", text_color="red"))
            print(f"ERRO: Não foi possível conectar ao backend em {API_CONSULTA_URL}")
        except requests.exceptions.Timeout:
            self.after(0, lambda: self.consulta_feedback_label.configure(text="Tempo esgotado na consulta da tabela.", text_color="red"))
            print("ERRO: Requisição de dados da COVID-19 (tabela) excedeu o tempo limite.")
        except requests.exceptions.RequestException as e:
            self.after(0, lambda: self.consulta_feedback_label.configure(text=f"Erro na consulta da tabela: {e}", text_color="red"))
            print(f"ERRO ao consultar dados da COVID-19 (tabela): {e}")
        except json.JSONDecodeError:
            self.after(0, lambda: self.consulta_feedback_label.configure(text="Erro no formato de dados do backend (tabela).", text_color="red"))
            print("ERRO: Resposta não é um JSON válido ao consultar dados da COVID-19 (tabela).")

    def _fetch_plot_data_async(self, params):
        """
        Função assíncrona para buscar dados para o gráfico.
        """
        try:
            response = requests.get(API_VISUALIZACAO_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # Verifique se os dados de base (datas, casos, óbitos) estão presentes,
            # ou se a agregação é multi-série.
            if "dates" in data and ("cases" in data or "labels" in data):
                self.plot_data = data
                self.after(0, self._render_plot)
                self.after(0, lambda: self.consulta_feedback_label.configure(text="Gráfico gerado com sucesso.", text_color="green"))
                self.after(0, self.show_plot_view)
            else:
                self.plot_data = {}
                self.after(0, self._render_plot)
                self.after(0, lambda: self.consulta_feedback_label.configure(text="Nenhum dado encontrado para o gráfico.", text_color="red"))
                self.after(0, self.show_plot_view)
                print("DEBUG: Estrutura de resposta inesperada para dados de visualização.")

        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self.consulta_feedback_label.configure(text="Erro de Conexão com o backend (gráfico).", text_color="red"))
            print(f"ERRO: Não foi possível conectar ao backend em {API_VISUALIZACAO_URL}")
        except requests.exceptions.Timeout:
            self.after(0, lambda: self.consulta_feedback_label.configure(text="Tempo esgotado na consulta do gráfico.", text_color="red"))
            print("ERRO: Requisição de dados para gráfico excedeu o tempo limite.")
        except requests.exceptions.RequestException as e:
            self.after(0, lambda: self.consulta_feedback_label.configure(text=f"Erro na consulta do gráfico: {e}", text_color="red"))
            print(f"ERRO ao consultar dados para gráfico: {e}")
        except json.JSONDecodeError:
            self.after(0, lambda: self.consulta_feedback_label.configure(text="Erro no formato de dados do backend (gráfico).", text_color="red"))
            print("ERRO: Resposta não é um JSON válido ao consultar dados para gráfico.")


    def _render_table(self):
        """
        Renderiza os dados na tabela dinâmica.
        """
        # Limpa a tabela existente
        for widget in self.table_widgets:
            widget.destroy()
        self.table_widgets.clear()

        # Configura as colunas da tabela
        for i, header_text in enumerate(self.table_headers):
            self.table_scroll_frame.grid_columnconfigure(i, weight=1)
            header_label = ctk.CTkLabel(self.table_scroll_frame, text=header_text, font=ctk.CTkFont(weight="bold"))
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            self.table_widgets.append(header_label)

        if not self.records:
            no_data_label = ctk.CTkLabel(self.table_scroll_frame, text="Nenhum dado para exibir com os filtros selecionados.")
            no_data_label.grid(row=1, column=0, columnspan=len(self.table_headers), padx=5, pady=20)
            self.table_widgets.append(no_data_label)
        else:
            for row_idx, record in enumerate(self.records):
                data_values = [
                    record.get("date", "N/A"),
                    record.get("state", "N/A"),
                    record.get("city", "N/A"),
                    record.get("confirmed_cases", "N/A"),
                    record.get("deaths", "N/A"),
                    record.get("new_cases", "N/A"),
                    record.get("new_deaths", "N/A")
                ]
                for col_idx, value in enumerate(data_values):
                    cell_label = ctk.CTkLabel(self.table_scroll_frame, text=str(value))
                    cell_label.grid(row=row_idx + 1, column=col_idx, padx=5, pady=2, sticky="ew")
                    self.table_widgets.append(cell_label)

        self._update_pagination_info()

    def _render_plot(self):
        """
        Renderiza o gráfico Matplotlib na interface, suportando diferentes tipos e agregações.
        """
        if self.plot_canvas:
            self.plot_canvas.get_tk_widget().destroy()
            self.plot_canvas = None
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None
        plt.close('all')

        fig, ax = plt.subplots(figsize=(8, 6))

         # 1. Pega o NOME da cor de fundo para o tema atual (ex: 'gray14' ou 'gray86')
        bg_color_name = self._apply_appearance_mode(self.cget("fg_color"))
        # 2. Usa o método winfo_rgb para converter o NOME para valores RGB (0-65535)
        #    e depois normaliza para o formato do Matplotlib (0.0-1.0)
        bg_color = [c / 65535 for c in self.winfo_rgb(bg_color_name)]

        # 3. Faz o mesmo processo para a cor do texto
        text_color_name = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        text_color = [c / 65535 for c in self.winfo_rgb(text_color_name)]

        # 4. Agora passa as cores no formato RGB para o Matplotlib
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        line_color_cases = "blue"
        line_color_deaths = "red"

        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        ax.spines['bottom'].set_color(text_color)
        ax.spines['top'].set_color(text_color)
        ax.spines['left'].set_color(text_color)
        ax.spines['right'].set_color(text_color)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        ax.legend(labelcolor=text_color)

        if self.plot_data and self.plot_data.get("dates"):
            dates = [datetime.strptime(d, '%Y-%m-%d') for d in self.plot_data["dates"]]
            chart_type = self.optionmenu_chart_type.get()
            aggregation = self.optionmenu_aggregation.get()

            if aggregation == 'Nenhum' or \
               (aggregation == 'Estado' and self.get_filter_params().get("estado")) or \
               (aggregation == 'Cidade' and self.get_filter_params().get("municipio")):
                # Plotagem de série única
                cases = self.plot_data["cases"]
                deaths = self.plot_data["deaths"]

                ax.plot(dates, cases, label='Casos', color=line_color_cases)
                ax.plot(dates, deaths, label='Óbitos', color=line_color_deaths)
            else:
                # Plotagem de múltiplas séries (por Estado ou Cidade)
                labels = self.plot_data.get("labels", [])
                for label in labels:
                    cases_data = self.plot_data.get(f"cases_{label}", [])
                    deaths_data = self.plot_data.get(f"deaths_{label}", [])
                    
                    # Filtra None values, pois podem vir de datas onde o dado não existe para aquele label
                    valid_dates_cases = [dates[i] for i, val in enumerate(cases_data) if val is not None]
                    valid_cases = [val for val in cases_data if val is not None]

                    valid_dates_deaths = [dates[i] for i, val in enumerate(deaths_data) if val is not None]
                    valid_deaths = [val for val in deaths_data if val is not None]

                    if valid_cases:
                        ax.plot(valid_dates_cases, valid_cases, label=f'Casos - {label}', linestyle='-')
                    if valid_deaths:
                        ax.plot(valid_dates_deaths, valid_deaths, label=f'Óbitos - {label}', linestyle='--')


            ax.set_xlabel("Data")
            ax.set_ylabel("Contagem")
            ax.set_title(f"Evolução de {chart_type} por {aggregation if aggregation != 'Nenhum' else 'Nacional'}")
            ax.legend(facecolor=bg_color, labelcolor=text_color)
            fig.autofmt_xdate()
        else:
            ax.text(0.5, 0.5, "Nenhum dado para exibir o gráfico.",
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax.transAxes, color=text_color, fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])

        self.plot_canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.plot_canvas_widget = self.plot_canvas.get_tk_widget()
        self.plot_canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.toolbar = NavigationToolbar2Tk(self.plot_canvas, self.plot_frame)
        self.toolbar.update()
        self.plot_canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)


    def _update_pagination_info(self):
        """Atualiza o texto do indicador de página e o estado dos botões de paginação."""
        self.label_pagina_info.configure(text=f"Página {self.current_page} de {self.total_pages}")
        self.button_anterior.configure(state="normal" if self.current_page > 1 else "disabled")
        self.button_proximo.configure(state="normal" if self.current_page < self.total_pages else "disabled")

    def previous_page(self):
        """Volta para a página anterior, se possível."""
        if self.current_page > 1:
            self.current_page -= 1
            self.perform_consulta()

    def next_page(self):
        """Avança para a próxima página, se possível."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.perform_consulta()

    def import_dataset(self):
        """
        Abre uma caixa de diálogo para seleção de arquivo e inicia o processo de importação.
        """
        # Desabilitar botões durante a operação
        self.button_importar.configure(state="disabled")
        self.button_atualizar.configure(state="disabled")
        self.button_limpar.configure(state="disabled")

        file_path = filedialog.askopenfilename(
            title="Selecionar Dataset COVID-19",
            filetypes=[("Arquivos CSV", ".csv"), ("Arquivos CSV GZ", ".csv.gz")]
        )
        if file_path:
            self.selected_file_path = file_path
            self.file_path_label.configure(text=f"Arquivo selecionado: {os.path.basename(file_path)}")
            self.gerenciamento_feedback_label.configure(text="Iniciando importação do dataset...", text_color="orange")
            threading.Thread(target=self._send_management_request_async,
                             args=(API_IMPORT_URL, "POST", {"file_path": self.selected_file_path},
                                   "Dataset importado com sucesso!", "Erro ao importar dataset.")).start()
        else:
            self.gerenciamento_feedback_label.configure(text="Importação cancelada.", text_color="blue")
            # Reabilitar botões
            self.button_importar.configure(state="normal")
            self.button_atualizar.configure(state="normal")
            self.button_limpar.configure(state="normal")


    def update_dataset(self):
        """
        Inicia o processo de atualização de dados existentes.
        """
        # Desabilitar botões durante a operação
        self.button_importar.configure(state="disabled")
        self.button_atualizar.configure(state="disabled")
        self.button_limpar.configure(state="disabled")

        self.gerenciamento_feedback_label.configure(text="Iniciando atualização dos dados...", text_color="orange")
        threading.Thread(target=self._send_management_request_async,
                         args=(API_UPDATE_URL, "PUT", {},
                               "Dados atualizados com sucesso!", "Erro ao atualizar dados.")).start()

    def clear_dataset(self):
        """
        Inicia o processo de limpeza da base de dados.
        """
        # Desabilitar botões durante a operação
        self.button_importar.configure(state="disabled")
        self.button_atualizar.configure(state="disabled")
        self.button_limpar.configure(state="disabled")

        # Usar ctk.CTk messagebox para confirmação
        dialog = ctk.CTkInputDialog(text="Tem certeza que deseja limpar toda a base de dados? Esta ação é irreversível! Digite 'SIM' para confirmar.", title="Confirmar Limpeza")
        user_input = dialog.get_input() # Retorna a string ou None se cancelar

        if user_input and user_input.upper() == "SIM":
            self.gerenciamento_feedback_label.configure(text="Limpando base de dados...", text_color="orange")
            threading.Thread(target=self._send_management_request_async,
                             args=(API_DELETE_URL, "DELETE", {},
                                   "Base de dados limpa com sucesso!", "Erro ao limpar base de dados.")).start()
        else:
            self.gerenciamento_feedback_label.configure(text="Limpeza cancelada.", text_color="blue")
            # Reabilitar botões
            self.button_importar.configure(state="normal")
            self.button_atualizar.configure(state="normal")
            self.button_limpar.configure(state="normal")


    def _send_management_request_async(self, url, method, json_data, success_msg, error_msg):
        """
        Função assíncrona genérica para enviar requisições de gerenciamento.
        """
        try:
            if method == "POST":
                response = requests.post(url, json=json_data)
            elif method == "PUT":
                response = requests.put(url, json=json_data)
            elif method == "DELETE":
                response = requests.delete(url)
            else:
                raise ValueError("Método HTTP inválido.")

            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                self.after(0, lambda: self.gerenciamento_feedback_label.configure(text=success_msg, text_color="green"))
                # Recarregar estados e consulta após operações de gerenciamento
                self.after(0, self.load_states)
                self.after(0, self.perform_consulta)
            else:
                self.after(0, lambda: self.gerenciamento_feedback_label.configure(text=f"{error_msg} Detalhes: {data.get('message', 'N/A')}", text_color="red"))

        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self.gerenciamento_feedback_label.configure(text=f"Erro de Conexão: {error_msg}", text_color="red"))
            print(f"ERRO: Não foi possível conectar ao backend em {url}")
        except requests.exceptions.Timeout:
            self.after(0, lambda: self.gerenciamento_feedback_label.configure(text=f"Tempo esgotado: {error_msg}", text_color="red"))
            print(f"ERRO: Requisição para {url} excedeu o tempo limite.")
        except requests.exceptions.RequestException as e:
            self.after(0, lambda: self.gerenciamento_feedback_label.configure(text=f"Erro na operação: {error_msg} ({e})", text_color="red"))
            print(f"ERRO na requisição para {url}: {e}")
        except ValueError as e:
            self.after(0, lambda: self.gerenciamento_feedback_label.configure(text=f"Erro interno: {e}", text_color="red"))
            print(f"ERRO interno: {e}")
        except json.JSONDecodeError:
            self.after(0, lambda: self.gerenciamento_feedback_label.configure(text=f"Erro no formato de dados do backend: {error_msg}", text_color="red"))
            print(f"ERRO: Resposta não é um JSON válido para {url}.")
        finally:
            # Reabilitar botões após a conclusão (sucesso ou falha)
            self.after(0, lambda: self.button_importar.configure(state="normal"))
            self.after(0, lambda: self.button_atualizar.configure(state="normal"))
            self.after(0, lambda: self.button_limpar.configure(state="normal"))


if __name__ == "__main__":
    app = App()
    # Agenda a execução do fluxo de login para ocorrer assim que o mainloop iniciar.
    # O delay de 1ms (ou 10ms) é apenas para garantir que o mainloop se estabeleça.
    app.after(1, app.iniciar_fluxo_de_login)
    app.mainloop()