# Desenho das páginas na placa de vídeo (GTX 1070 Ti, 8 GB).
#
# Modelo: Stable Diffusion XL base 1.0 + o estilo "livro de colorir"
# (LoRA ColoringBookRedmond V2), com o VAE corrigido para float16 (o VAE
# original do SDXL gera imagem preta em float16). Para caber nos 8 GB, cada
# parte do modelo só vai para a placa na hora de trabalhar.
#
# Personagens próprios: com uma imagem de referência do personagem, o
# IP-Adapter ajuda a manter a mesma aparência em todas as páginas.
#
# Os modelos são baixados uma vez para a pasta de modelos (HF_HOME).
import time

PADRAO = {
    'modelo_base': 'stabilityai/stable-diffusion-xl-base-1.0',
    'vae': 'madebyollin/sdxl-vae-fp16-fix',
    'lora': 'artificialguybr/ColoringBookRedmond-V2',
    'lora_arquivo': 'ColoringBookRedmond-ColoringBook-ColoringBookAF.safetensors',
    'lora_peso': 1.0,
    'gatilho': 'ColoringBookAF, Coloring Book',
    'ip_adapter': 'h94/IP-Adapter',
    'ip_adapter_pasta': 'sdxl_models',
    'ip_adapter_arquivo': 'ip-adapter_sdxl.safetensors',
    'precisao': 'float16',
    'passos': 30,
    'guia': 7.0,
    # 768 x 1088 tem a proporção do A4 (0,706) e é múltiplo de 64
    'largura': 768,
    'altura': 1088,
}

SUFIXO = ('black and white coloring book page for kids, thick clean outlines, closed shapes, '
          'pure white background, no shading, no gray, no text')
NEGATIVO = ('color, colored, gray, grey, shading, shadows, gradient, halftone, crosshatching, '
            'texture, noise, sketch, messy lines, broken lines, text, letters, watermark, signature, '
            'logo, frame, border, cropped, cut off, blurry, photo, realistic, 3d render, '
            'deformed hands, extra fingers, extra limbs, distorted face')


class Desenhista:
    def __init__(self, config=None, com_personagem=False):
        import torch
        from diffusers import AutoencoderKL, StableDiffusionXLPipeline

        self.cfg = {**PADRAO, **(config or {})}
        tipo = torch.float16 if self.cfg['precisao'] == 'float16' else torch.float32
        vae = AutoencoderKL.from_pretrained(self.cfg['vae'], torch_dtype=tipo)
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            self.cfg['modelo_base'], vae=vae, torch_dtype=tipo, use_safetensors=True,
            variant='fp16' if tipo == torch.float16 else None)
        self.pipe.load_lora_weights(self.cfg['lora'], weight_name=self.cfg['lora_arquivo'], adapter_name='colorir')
        self.pipe.set_adapters(['colorir'], adapter_weights=[self.cfg['lora_peso']])
        self.com_personagem = com_personagem
        if com_personagem:
            self.pipe.load_ip_adapter(self.cfg['ip_adapter'], subfolder=self.cfg['ip_adapter_pasta'],
                                      weight_name=self.cfg['ip_adapter_arquivo'])
        self.pipe.enable_model_cpu_offload()
        self.pipe.enable_vae_tiling()
        self.torch = torch

    def desenhar(self, prompt, semente, negativo_extra='', referencia=None, forca=0.6):
        """Gera uma imagem (PIL) e devolve (imagem, segundos)."""
        from PIL import Image

        inicio = time.time()
        texto = f"{self.cfg['gatilho']}, {prompt}, {SUFIXO}"
        negativo = NEGATIVO + (', ' + negativo_extra if negativo_extra else '')
        extra = {}
        if self.com_personagem:
            if referencia:
                self.pipe.set_ip_adapter_scale(forca)
                extra['ip_adapter_image'] = Image.open(referencia).convert('RGB')
            else:
                # Página sem personagem: desliga a influência da referência
                self.pipe.set_ip_adapter_scale(0.0)
                extra['ip_adapter_image'] = Image.new('RGB', (224, 224), 'white')
        imagem = self.pipe(
            prompt=texto, negative_prompt=negativo,
            width=self.cfg['largura'], height=self.cfg['altura'],
            num_inference_steps=self.cfg['passos'], guidance_scale=self.cfg['guia'],
            generator=self.torch.Generator('cpu').manual_seed(int(semente)), **extra,
        ).images[0]
        # Devolve a placa entre uma página e outra, para o estúdio poder usá-la
        self.pipe.maybe_free_model_hooks()
        if self.torch.cuda.is_available():
            self.torch.cuda.empty_cache()
        return imagem.convert('L'), time.time() - inicio
