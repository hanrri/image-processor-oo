import tkinter as tk
from tkinter import messagebox, filedialog
import os
import requests
from io import BytesIO
from PIL import Image, ImageTk, ImageFilter, ImageOps, ImageEnhance

class Imagem:
    def __init__(self, fonte, tipo="local"):
        self.caminho_original = "imagem_downloaded.jpg"
        self._pil_image = None
        
        try:
            if tipo == "local":
                self.caminho_original = fonte
                self._pil_image = Image.open(fonte)
            elif tipo == "bytes":
                self._pil_image = Image.open(BytesIO(fonte))
            
            if self._pil_image.mode != 'RGB':
                self._pil_image = self._pil_image.convert('RGB')
                
        except Exception as e:
            raise ValueError(f"Erro ao processar imagem: {str(e)}")

    def get_pil_image(self):
        return self._pil_image.copy()

    def get_nome_base(self):
        nome = os.path.basename(self.caminho_original)
        nome_sem_ext, _ = os.path.splitext(nome)
        return nome_sem_ext if nome_sem_ext else "imagem"

    def salvar(self, imagem_processada, nome_filtro):
        nome_base = self.get_nome_base()
        novo_nome = f"{nome_base}_{nome_filtro}.jpg"
        caminho_salvar = os.path.join(os.getcwd(), novo_nome)
        
        try:
            imagem_processada.save(caminho_salvar)
            return caminho_salvar
        except Exception as e:
            raise IOError(f"Não foi possível salvar a imagem: {e}")

class Download:
    def buscar(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            response.raise_for_status()
            
            if 'image' not in response.headers.get('content-type', ''):
                raise ValueError("A URL não contém uma imagem válida.")
                
            return Imagem(response.content, tipo="bytes")
        except Exception as e:
            raise Exception(f"Falha no download: {e}")

class FiltroEscalaCinza:
    def aplicar(self, imagem_obj):
        original = imagem_obj.get_pil_image()
        return ImageOps.grayscale(original).convert("RGB")

class FiltroPretoBranco:
    def aplicar(self, imagem_obj):
        original = imagem_obj.get_pil_image().convert("L")
        return original.point(lambda x: 0 if x < 128 else 255, '1').convert("RGB")

class FiltroNegativo:
    def aplicar(self, imagem_obj):
        original = imagem_obj.get_pil_image()
        return ImageOps.invert(original)

class FiltroBlurred:
    def aplicar(self, imagem_obj):
        original = imagem_obj.get_pil_image()
        return original.filter(ImageFilter.GaussianBlur(radius=5))

class FiltroContorno:
    def aplicar(self, imagem_obj):
        original = imagem_obj.get_pil_image()
        return original.filter(ImageFilter.CONTOUR)

class FiltroCartoon:
    def aplicar(self, imagem_obj):
        original = imagem_obj.get_pil_image()
        img_quantized = ImageOps.posterize(original, 2)
        edges = original.filter(ImageFilter.FIND_EDGES).convert("L")
        edges = ImageOps.invert(edges)
        enhancer = ImageEnhance.Contrast(edges)
        edges = enhancer.enhance(8.0).convert("1")
        return img_quantized.filter(ImageFilter.SMOOTH)

class Principal:
    def __init__(self, root):
        self.root = root
        self.root.title("Processador de Imagens OO")
        self.root.geometry("900x750")
        
        self.imagem_atual_obj = None
        self.imagem_exibicao = None
        
        self._configurar_interface()

    def _configurar_interface(self):
        frame_topo = tk.Frame(self.root, pady=10, padx=10, bg="#e0e0e0")
        frame_topo.pack(fill=tk.X, side=tk.TOP)
        
        tk.Label(frame_topo, text="Caminho ou URL:", bg="#e0e0e0").pack(side=tk.LEFT)
        self.entrada_path = tk.Entry(frame_topo, width=50)
        self.entrada_path.pack(side=tk.LEFT, padx=10)
        
        tk.Button(frame_topo, text="Carregar", command=self.carregar_imagem, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(frame_topo, text="...", command=self.buscar_arquivo_local).pack(side=tk.LEFT)

        frame_extra = tk.Frame(self.root, pady=15, bg="#f0f0f0")
        frame_extra.pack(side=tk.BOTTOM, fill=tk.X)
        
        tk.Button(frame_extra, text="LISTAR Arquivos", command=self.listar_arquivos).pack(side=tk.LEFT, padx=20)
        tk.Button(frame_extra, text="LIMPAR / INÍCIO", command=self.limpar_tela, bg="#FFC107", fg="black").pack(side=tk.LEFT, padx=20)
        tk.Button(frame_extra, text="SAIR", command=self.root.quit, bg="#FF5722", fg="white").pack(side=tk.RIGHT, padx=20)

        frame_botoes = tk.Frame(self.root, pady=10)
        frame_botoes.pack(side=tk.BOTTOM, fill=tk.X)
        
        tk.Label(frame_botoes, text="Filtros:", font=("Arial", 10, "bold")).pack(pady=(0,5))
        
        grid_filtros = tk.Frame(frame_botoes)
        grid_filtros.pack()

        filtros = [
            ("Escala de Cinza", FiltroEscalaCinza()),
            ("Preto e Branco", FiltroPretoBranco()),
            ("Cartoon", FiltroCartoon()),
            ("Negativo", FiltroNegativo()),
            ("Contorno", FiltroContorno()),
            ("Blurred", FiltroBlurred())
        ]
        
        for i, (nome, classe_filtro) in enumerate(filtros):
            tk.Button(grid_filtros, text=nome, width=15, pady=5,
                      command=lambda f=classe_filtro, n=nome: self.aplicar_filtro(f, n)
                      ).grid(row=0, column=i, padx=5)

        self.lbl_info = tk.Label(self.root, text="Nenhuma imagem carregada", font=("Arial", 12))
        self.lbl_info.pack(side=tk.TOP, pady=5)
        
        self.canvas_area = tk.Label(self.root, bg="gray")
        self.canvas_area.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

    def buscar_arquivo_local(self):
        filename = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg;*.png;*.jpeg")])
        if filename:
            self.entrada_path.delete(0, tk.END)
            self.entrada_path.insert(0, filename)
            self.carregar_imagem()

    def carregar_imagem(self):
        entrada = self.entrada_path.get().strip()
        if not entrada:
            messagebox.showwarning("Aviso", "Por favor, insira uma URL ou caminho de arquivo.")
            return

        try:
            self.lbl_info.config(text="Carregando...")
            self.root.update_idletasks()

            if entrada.startswith("http://") or entrada.startswith("https://"):
                downloader = Download()
                self.imagem_atual_obj = downloader.buscar(entrada)
            else:
                entrada = entrada.replace('"', '').replace("'", "")
                self.imagem_atual_obj = Imagem(entrada, tipo="local")
            
            self._atualizar_preview(self.imagem_atual_obj.get_pil_image())
            self.lbl_info.config(text=f"Imagem carregada: {os.path.basename(entrada)}")
            
        except Exception as e:
            self.lbl_info.config(text="Erro ao carregar")
            messagebox.showerror("Erro", str(e))

    def aplicar_filtro(self, objeto_filtro, nome_filtro):
        if not self.imagem_atual_obj:
            messagebox.showwarning("Aviso", "Carregue uma imagem primeiro.")
            return

        try:
            self.lbl_info.config(text=f"Aplicando filtro: {nome_filtro}...")
            self.root.update_idletasks()
            
            imagem_filtrada_pil = objeto_filtro.aplicar(self.imagem_atual_obj)
            
            sufixo = nome_filtro.lower().replace(" ", "_")
            caminho_salvo = self.imagem_atual_obj.salvar(imagem_filtrada_pil, sufixo)
            
            self._atualizar_preview(imagem_filtrada_pil)
            self.lbl_info.config(text=f"Sucesso! Salvo em: {os.path.basename(caminho_salvo)}")
            messagebox.showinfo("Sucesso", f"Filtro aplicado e imagem salva:\n{os.path.basename(caminho_salvo)}")
            
        except Exception as e:
            messagebox.showerror("Erro no filtro", str(e))

    def _atualizar_preview(self, pil_image):
        max_w, max_h = 800, 450 
        
        img_copy = pil_image.copy()
        img_copy.thumbnail((max_w, max_h))
        
        self.imagem_exibicao = ImageTk.PhotoImage(img_copy)
        self.canvas_area.config(image=self.imagem_exibicao)

    def listar_arquivos(self):
        diretorio_atual = os.getcwd()
        arquivos = [f for f in os.listdir(diretorio_atual) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        texto_lista = "\n".join(arquivos) if arquivos else "Nenhuma imagem encontrada."
        
        janela_lista = tk.Toplevel(self.root)
        janela_lista.title("Arquivos no Diretório Atual")
        
        tk.Label(janela_lista, text=f"Diretório: {diretorio_atual}", font=("Arial", 10, "bold")).pack(pady=5)
        
        text_area = tk.Text(janela_lista, width=60, height=20)
        text_area.pack(padx=10, pady=10)
        text_area.insert(tk.END, texto_lista)
        text_area.config(state=tk.DISABLED)

    def limpar_tela(self):
        self.imagem_atual_obj = None
        self.imagem_exibicao = None
        self.canvas_area.config(image="") 
        self.entrada_path.delete(0, tk.END)
        self.lbl_info.config(text="Nenhuma imagem carregada")

if __name__ == "__main__":
    root = tk.Tk()
    app = Principal(root)
    root.mainloop()