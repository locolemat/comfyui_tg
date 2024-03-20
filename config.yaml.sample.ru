network:
  BOT_TOKEN: 'xxx:xxxxxx'
  SERVER_ADDRESSES: 
    - "127.0.0.1:8188"
    - "127.0.0.1:8189"
    - "127.0.0.1:8190"

bot:
  TRANSLATE: True
  INITIAL_TOKEN_AMOUNT: 10
  DENY_TEXT: "Access denied"
  USER_CONFIGS_LOCATION: "user_configs"
  START_TEXT: ""
  IMAGE_TO_VIDEO_TEXT: ""
  VIDEO_PRICE: 5
  IMAGE_PRICE: 1
  CHOOSE_ASPECT_RATIO: ""
  HELP_TEXT: "Для генерации можно использовать текст на русском языке

По-умолчанию каритнка создаётся в разрешении 512x512 пикселей

В промпте можно указать размер ШИРИНАxВЫСОТА. Например - 1024x512

Для добавления негативного промпта - добавить его в конец сообщения через разделитель '|'

Команды:

/models - список моделей

/loras - спимок LoRA

/upscale .... - создаст картинку высокого разрешения

/face .... - исправит дефекты лиц"

comfyui:
  DEFAULT_MODEL: 'revAnimatedFp16_122.safetensors'
  DEFAULT_CONTROLNET: 'control_v11f1e_sd15_tile.pth'
  DEFAULT_VAE: 'vaeFtMse840000Ema_v10.safetensors'
  DEFAULT_UPSCALER: '4xNMKDSuperscale_4xNMKDSuperscale.pt'
  SCHEDULER: 'karras'                 
  SAMPLER: 'uni_pc'
  SAMPLER_STEPS: 30
  MAX_STEPS: 100
  TOKEN_MERGE_RATIO: '0.6'
  CLIP_SKIP: '-1'
  CONTROLNET_STRENGTH: '1.0'
  DEFAULT_WIDTH: 512
  DEFAULT_HEIGHT: 512
  MAX_WIDTH: 2048      
  MAX_HEIGHT: 2048
  BEAUTIFY_PROMPT: ',masterpiece, perfect, small details, highly detailed, best, high quality, professional photo'
  NEGATIVE_PROMPT: 'low quality, worst quality, embedding:badhandv4, blurred, deformed, embedding:EasyNegative, embedding:badquality, watermark, text, font, signage, artist name, text, caption, jpeg artifacts'

whitelist:

loras:
  - 'vlozhkin|vlozhkin3.safetensors|1|vlozhkin style illustration'
  - 'jh|jamie_hewlett_style.safetensors|1|jamie hewlett style'
  - 'minecraft|minecraft_square_style_v2-10.safetensors|1|minecraft square style'
  - 'giardino|Giardino_Style-13.safetensors|1|giardino style illustration'
  - 'akashiba|aka_shiba_offset.safetensors|1|'
  - 'alien|alien_lora.safetensors|0.5|alien, professional photo'
  - 'c4t|c4tt4stic6(1).safetensors|0.9|c4tt4stic cat'

models:
  - 'rev|revAnimatedFp16_122.safetensors'
  - 'rel|Reliberate.safetensors'
  - 'jug|juggernaut_aftermath.safetensors'

