#!/usr/bin/env python

import io
import logging
import os, sys
import coloredlogs
import aiohttp
import asyncio

logging.basicConfig(filename='bot.log', encoding='utf-8')

log = logging.getLogger()
coloredlogs.install(level=logging.INFO, logger=log, fmt='%(levelname)s %(message)s')

if not os.path.exists('config.yaml'):
    log.critical("No config.yaml file found!")
    sys.exit(os.EX_CONFIG) 

import pickle 
import time
import copy
import re
import io
import asyncio
import telebot
from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Chat, WebAppInfo
from telebot.util import quick_markup
from telebot.asyncio_storage import StateMemoryStorage
from states import BotStates
import random
from PIL import Image
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance
import websocket
import uuid
import json
import yaml
import urllib.request
import urllib.parse
from sanitize_filename import sanitize

from server_address import ServerAddress, ServerAddressController
from queue_system import Queue, QueueItem
from exception_handler import ErrHandler
from robokassa import check_signature_result, check_success_payment, calculate_signature, generate_payment_link, generate_payment_data
from database import DB
from user_configs import add_config, update_config, read_config


payments_db = DB(path='payments.sqlite3')
with open('config.yaml') as f:
    config = yaml.safe_load(f)
    BOT_TOKEN = config['network']['BOT_TOKEN']
    SERVER_ADDRESSES = ServerAddressController([ServerAddress(ADDRESS) for ADDRESS in config['network']['SERVER_ADDRESSES']])
    QUEUE = Queue()
    TRANSLATE = config['bot']['TRANSLATE']
    HELP_TEXT = config['bot']['HELP_TEXT']
    START_TEXT = config['bot']['START_TEXT']
    IMAGE_TO_VIDEO_TEXT = config['bot']['IMAGE_TO_VIDEO_TEXT']
    IMAGE_PRICE = config['bot']['IMAGE_PRICE']
    VIDEO_PRICE = config['bot']['VIDEO_PRICE']
    DENY_TEXT = config['bot']['DENY_TEXT']
    CHOOSE_ASPECT_RATIO = config['bot']['CHOOSE_ASPECT_RATIO']

    MERCHANT_LOGIN = config['payment']['MERCHANT_LOGIN']
    MERCHANT_PASSWORD_1 = config['payment']['MERCHANT_PASSWORD_1']
    COST = config['payment']['COST']
    PAYMENT_DESC = config['payment']['DESCRIPTION']

    DEFAULT_MODEL = config['comfyui']['DEFAULT_MODEL']
    DEFAULT_VAE = config['comfyui']['DEFAULT_VAE']
    DEFAULT_CONTROLNET = config['comfyui']['DEFAULT_CONTROLNET']
    CONTROLNET_STRENGTH = config['comfyui']['CONTROLNET_STRENGTH']
    DEFAULT_UPSCALER = config['comfyui']['DEFAULT_UPSCALER']
    NEGATIVE_PROMPT = config['comfyui']['NEGATIVE_PROMPT']
    BEAUTIFY_PROMPT = config['comfyui']['BEAUTIFY_PROMPT']
    DEFAULT_WIDTH = config['comfyui']['DEFAULT_WIDTH']
    DEFAULT_HEIGHT = config['comfyui']['DEFAULT_HEIGHT']
    MAX_WIDTH = config['comfyui']['MAX_WIDTH']
    MAX_HEIGHT = config['comfyui']['MAX_HEIGHT']
    SCHEDULER = config['comfyui']['SCHEDULER']
    SAMPLER = config['comfyui']['SAMPLER']
    SAMPLER_STEPS = config['comfyui']['SAMPLER_STEPS']
    MAX_STEPS = config['comfyui']['MAX_STEPS']
    TOKEN_MERGE_RATIO = config['comfyui']['TOKEN_MERGE_RATIO']
    CLIP_SKIP = config['comfyui']['CLIP_SKIP']
    #ALLOW_DIRECT_LORA = config['comfyui']['ALLOW_DIRECT_LORA']


filtered_words = []

if os.path.exists('./word_filter.yaml'):
    with open('word_filter.yaml', encoding='utf-8') as f:
        words = yaml.safe_load(f)
        for word in words['words']:
            filtered_words.append(word)

if not os.path.exists('upload'):
    log.info("Creating upload folder")
    os.makedirs('upload')

if not os.path.exists('generated'):
    log.info("Creating generated folder")
    os.makedirs('generated')

if (config['whitelist'] is None): # Allow all, whitelist is empty
    log.warning("Whitelist is empty, all users allowed to access this bot! Modify config.yaml")
    whitelist = None
else:
    whitelist = config['whitelist']

with open('blacklist.yaml') as f:
    b_config = yaml.safe_load(f)

blacklist = None
if b_config['blacklist'] is not None:
    blacklist = b_config['blacklist']

if os.path.exists('chat_face.pkl'):
    with open('chat_face.pkl', 'rb') as f:
        chat_face = pickle.load(f)
        if (len(chat_face) > 0):
            log.info('Loaded chat faces')
else:
    chat_face = {}

if os.path.exists('chat_style.pkl'):
    with open('chat_style.pkl', 'rb') as f:
        chat_style = pickle.load(f)
        if (len(chat_style) > 0):
            log.info('Loaded chat styles')
else:
    chat_style = {}


loras = []
if (config['loras'] is not None): # Has loras
    for lora in config['loras']:
        tmp = lora.split('|')
        if (len(tmp) == 4):
            log.info('Add LoRA - ' + tmp[1])
            loras.append({
                'name': tmp[0],
                'lora_file': tmp[1],
                'strength': tmp[2],
                'prompt': tmp[3]
                })

models = []
if (config['models'] is not None): # Has models
    for model in config['models']:
        tmp = model.split('|')
        if (len(tmp) == 2):
            log.info('Add model - ' + tmp[1])
            models.append({
                'name': tmp[0],
                'model_file': tmp[1]
                })
            

def get_lora(prompt):
    lr = re.findall('\\#\\w+\\:?\\d*.?\\d*\\s', prompt)

    if lr:
        lr = lr[0].replace('#', '').strip()
        if (":" in lr): # strength
            tmp = lr.split(':')
            lr = tmp[0]
            strength = tmp[1]
            if ("." not in strength):
                strength = strength + '.0'
        else:
            strength = None
        for lora in loras:
            if lora['name'] == lr:
                if strength:
                    lora = copy.deepcopy(lora)
                    lora['strength'] = strength
                log.info("Lora: " + lora['name'] + ' ' + lora['lora_file'])
                return lora
    return False


def get_model(prompt):
    md = re.findall('\\@\\w+', prompt)

    if md:
        md = md[0].replace('@', '').strip()
        for model in models:
            if model['name'] == md:
                log.info("Model: " + model['name'] + ' ' + model['model_file'])
                return model
    return {'model_file' : DEFAULT_MODEL, 'name' : DEFAULT_MODEL}


client_id = str(uuid.uuid4())

bot = AsyncTeleBot(BOT_TOKEN, state_storage=StateMemoryStorage(), exception_handler=ErrHandler())
aspect_ratios = {}

def cmt():
    return round(time.time() * 1000)

with open('workflows/t2v.json') as json_file:
    wf_noupscale = json.load(json_file)

with open('workflows/wf_upscale.json') as json_file:
    wf_upscale = json.load(json_file)


async def notify_of_queue_change():
    for item in QUEUE.get_items():
        await bot.send_message(chat_id=item.get_user(), text=f'Your position in the queue is now {QUEUE.determine_pos(item)}!')
        if QUEUE.determine_pos(item) == 0:
            chat = Chat(id=item.get_user(), type='private', username=item.get_username())

            await bot.send_message(chat_id=chat.id, text=f"It's your turn to generate now!")
            await bot.set_state(chat.id, BotStates.generate)
            
            await comfy(chat, item.get_prompt(), {})
            

async def check_access(id):
    if (blacklist is not None and id in blacklist):
        await bot.send_message(chat_id=id, text='You\'ve been blacklisted!')
        return False

    if (whitelist is None or len(whitelist) == 0): # Allow all, whitelist is empty
        log.info("Access allowed for %s, empty whitelist in config yaml", id)
        
        return True

    if (id in whitelist):
        log.info("Access allowed for %s, user in whitelist", id)
        return True

    await bot.send_message(chat_id=id, text=DENY_TEXT + "\nJoin AIDA's chat: https://t.me/AIDA_Generation")

    log.warning("Access denied for %s, user not in whitelist", id)
    return False


def configure(prompt, cfg):  
    config = cfg
    config['lora'] = get_lora(prompt)
    config['model'] = get_model(prompt)

    if ('/face' in prompt):
        prompt = prompt.replace('/face', '')
        config['facefix'] = True
    else:
        config['facefix'] = False

    if ('/upscale' in prompt):
        prompt = prompt.replace('/upscale', '')

    if config['lora']:
        prompt = config['lora']['prompt'] + ',' + prompt
        prompt = prompt.replace('#' + config['lora']['name'], '')

    if config['model']:
        prompt = prompt.replace('@' + config['model']['name'], '')

    sizes = re.findall('\d+x\d+', prompt)
    if sizes:
        dimensions = sizes[0].split('x')
        config['width'] = int(dimensions[0])
        config['height'] = int(dimensions[1])
        prompt = prompt.replace(sizes[0], '')
        if (config['width'] > MAX_WIDTH):
            config['width'] = MAX_WIDTH
        if (config['height'] > MAX_HEIGHT):
            config['height'] = MAX_HEIGHT
    else:
        config['width'] = DEFAULT_WIDTH
        config['height'] = DEFAULT_HEIGHT

    steps = re.findall('\\%\\d+', prompt)
    if steps:
        prompt = prompt.replace(steps[0], '')
        config['steps'] = int(steps[0].replace('%', ''))
        if (config['steps'] > MAX_STEPS):
            config['steps'] = MAX_STEPS
    else:
        config['steps'] = SAMPLER_STEPS

    cn_strength = re.findall('\\$\\d*.?\\d*', prompt)
    if cn_strength:
        prompt = prompt.replace(cn_strength[0], '')
        config['cn_strength'] = cn_strength[0].replace('$', '').replace(' ', '')
        if ("." not in config['cn_strength']):
            config['cn_strength'] = config['cn_strength'] + '.0'
    else:
        config['cn_strength'] = CONTROLNET_STRENGTH

    ipa_strength = re.findall('\\&\\d*.?\\d*', prompt)
    if ipa_strength:
        prompt = prompt.replace(ipa_strength[0], '')
        config['ipa_strength'] = ipa_strength[0].replace('&', '').replace(' ', '')
        if ("." not in config['ipa_strength']):
            config['ipa_strength'] = config['ipa_strength'] + '.0'
    else:
        config['ipa_strength'] = CONTROLNET_STRENGTH
    config['seed'] = random.randint(1, 18446744073709519872)

    if TRANSLATE:
        prompt = GoogleTranslator(source='auto', target='en').translate(text=prompt)

    if ('|' in prompt): #got negative prompt part
        ps = prompt.split('|')
        if not lora:
            prompt = ps[0].strip() + BEAUTIFY_PROMPT
        else:
            prompt = ps[0].strip()
        negative_prompt = ps[1].strip()
    else:
        if not lora:
            prompt = prompt + BEAUTIFY_PROMPT
        else:
            prompt = prompt.strip()
        negative_prompt = NEGATIVE_PROMPT

    if (config['id'] in chat_face):
        config['face_image'] = chat_face[config['id']]['file']
        config['face_weight'] = chat_face[config['id']]['weight']
        config['face'] = True  
    else:
        config['face_image'] = os.getcwd() + '/assets/blank.png'
        config['face_weight'] = 0
        config['face'] = False

    if (config['id'] in chat_style):
        config['style_image'] = chat_style[config['id']]['file']
        config['style_weight'] = chat_style[config['id']]['weight']
        config['style'] = True  
    else:
        config['style_image'] = os.getcwd() + '/assets/blank.png'
        config['style_weight'] = 0
        config['style'] = False
        
    if (not 'source_image' in config):
        config['source_image'] = os.getcwd() + '/assets/blank.png'
        config['cn_strength'] = 0

    if (not config['face'] and not config['style']):
        config['ipa_strength'] = 0

    return prompt, negative_prompt, config


def setup_workflow(prompt, config):
    if ('/upscale' in prompt):
        workflow = copy.deepcopy(wf_upscale)
    else:
        workflow = copy.deepcopy(wf_noupscale)

    prompt, negative_prompt, config = configure(prompt, config)
    
    for node in workflow:
        # if ("ckpt_name" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['ckpt_name'] = config['model']['model_file']

        # if ("vae_name" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['vae_name'] = DEFAULT_VAE

        # if ("control_net_name" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['control_net_name'] = DEFAULT_CONTROLNET

        # if ("strength" in workflow[node]['inputs']):
        #     if (workflow[node]['class_type'] == 'ControlNetApply'):
        #        workflow[node]['inputs']['strength'] = config['cn_strength']

        # if ("weight" in workflow[node]['inputs']):
        #     if (workflow[node]['class_type'] == 'IPAdapterApply'): # face-5 style-31
        #         if (node == "5"): #face
        #             if (config['face']):
        #                 workflow[node]['inputs']['weight'] = config['face_weight']
        #             else:
        #                 workflow[node]['inputs']['weight'] = 0
        #         if (node == "31"): #style
        #             if (config['style']):
        #                 workflow[node]['inputs']['weight'] = config['style_weight']
        #             else:
        #                 workflow[node]['inputs']['weight'] = 0

        # if ("width" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['width'] = config['width']

        # if ("height" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['height'] = config['height']

        # if ("seed" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['seed'] = config['seed']

        # if ("noise_seed" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['noise_seed'] = config['seed']

        # if ("sampler_name" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['sampler_name'] = SAMPLER

        # if ("scheduler" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['scheduler'] = SCHEDULER

        # if ("steps" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['steps'] = config['steps']
            
        # if ("stop_at_clip_layer" in workflow[node]['inputs']):
        #     workflow[node]['inputs']['stop_at_clip_layer'] = CLIP_SKIP


        if ("text" in workflow[node]['inputs']):
            if (workflow[node]['inputs']['text'] == 'positive prompt'):
               workflow[node]['inputs']['text'] = prompt

        # if ("text" in workflow[node]['inputs']):
        #     if (workflow[node]['inputs']['text'] == 'negative prompt'):
        #        workflow[node]['inputs']['text'] = negative_prompt

        # if ("image" in workflow[node]['inputs']):
        #     if (workflow[node]['inputs']['image'] == 'source image'):
        #        workflow[node]['inputs']['image'] = config['source_image']

        #     if (workflow[node]['inputs']['image'] == 'face image'):
        #        workflow[node]['inputs']['image'] = config['face_image']

        #     if (workflow[node]['inputs']['image'] == 'style image'):
        #        workflow[node]['inputs']['image'] = config['style_image']

        # if ("model_name" in workflow[node]['inputs']):
        #     if (workflow[node]['class_type'] == 'UpscaleModelLoader'):
        #        workflow[node]['inputs']['model_name'] = DEFAULT_UPSCALER
        
        # if ("ratio" in workflow[node]['inputs']):
        #     if (workflow[node]['class_type'] == 'TomePatchModel'):
        #        workflow[node]['inputs']['ratio'] = TOKEN_MERGE_RATIO

        # if ("lora_name" in workflow[node]['inputs']):
        #     if config['lora']:
        #         workflow[node]['inputs']['lora_name'] = config['lora']['lora_file']
        #         workflow[node]['inputs']['strength_model'] = config['lora']['strength']
        #         workflow[node]['inputs']['strength_clip'] = 1
        #     else:
        #         workflow[node]['inputs']['lora_name'] = 'default_lora.safetensors'
        #         workflow[node]['inputs']['strength_model'] = 0
        #         workflow[node]['inputs']['strength_clip'] = 0

        # if ("bbox_threshold" in workflow[node]['inputs']):
        #     if config['facefix']:
        #         workflow[node]['inputs']['bbox_threshold'] = 0.75
        #     else:
        #         workflow[node]['inputs']['bbox_threshold'] = 1

#    print(json.dumps(workflow, indent=2))

    return workflow

def queue_prompt(prompt, address):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(address), data=data)
    return json.loads(urllib.request.urlopen(req).read())


async def get_image(filename, subfolder, folder_type, address, session):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    async with session.get(f"http://{address}/view?{url_values}") as response:
        return await response.read()

async def get_history(prompt_id, address, session):
    async with session.get(f"http://{address}/history/{prompt_id}") as response:
        return await response.json()

async def get_images(ws, prompt, address, session):
    prompt_id = queue_prompt(prompt, address)['prompt_id']
    output_images = {}
    async for out in ws:
        if out is not None:
            message = json.loads(out.data)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    async with aiohttp.ClientSession() as session:
        history = await get_history(prompt_id, address, session)
        history = history[prompt_id]
        for o in history['outputs']:
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                images_output = []
                if 'images' in node_output:
                    for image in node_output['images']:
                        image_data = await get_image(image['filename'], image['subfolder'], image['type'], address, session)
                        images_output.append(image_data)
                output_images[node_id] = images_output

    return output_images

async def get_video(ws, prompt, address, session):
    prompt_id = queue_prompt(prompt, address)['prompt_id']
    output_videos = {}
    async for out in ws:
        if out is not None:
            message = json.loads(out.data)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    async with aiohttp.ClientSession() as session:
        history = await get_history(prompt_id, address, session)
        history = history[prompt_id]
        for o in history['outputs']:
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                videos_output = []
                if 'gifs' in node_output:
                    for video in node_output['gifs']:
                        video_data = await get_image(video['filename'], video['subfolder'], video['type'], address, session)
                        videos_output.append(video_data)
                output_videos[node_id] = videos_output

    return output_videos

async def comfy(chat, prompts, cfg):
    if not await check_access(chat.id):
        return

    # SERVERS = SERVER_ADDRESSES.servers()
    # SERVER_ADDRESS = None
    # queue_item = None
    
    # for SERVER in SERVERS:
    #     queue_item = SERVER.get_queue().find_queue_item_by_user(chat.id)
    #     if queue_item:
    #         SERVER_ADDRESS = SERVER
    #         prompts = queue_item.get_prompt()
        


    # if SERVER_ADDRESS is None:
    #     SERVER_ADDRESS = SERVER_ADDRESSES.find_shortest_queue()

    #     queue_item = QueueItem(SERVER_ADDRESS, chat.id, prompts, chat.username)
    #     queue = SERVER_ADDRESS.get_queue()
    #     queue.add_to_queue(queue_item)
    
    # if queue_item is None:
    #     await bot.send_message(chat_id=chat.id, text='There\'s been a problem trying to determine your position in the queue. Please, try again later.')
    #     print(f'SERVER: {SERVER_ADDRESS.address()}, QUEUE:{SERVER_ADDRESS.get_queue().get_items()}')
    #     return
    
    # print(f'SERVER: {SERVER_ADDRESS.address()}, QUEUE:{SERVER_ADDRESS.get_queue().get_items()}')

    # queue_position = SERVER_ADDRESS.get_queue().determine_pos(queue_item)
    # if queue_position != 0:
    #     await bot.send_message(chat_id=chat.id, text=f'Your current queue position is {queue_position}. We will notify you when that changes.')
    #     return
    # else:
    #     await bot.send_message(chat_id=chat.id, text=f'AIDA is currently working on your prompt.')
    
    SERVER_ADDRESS = SERVER_ADDRESSES.find_available_server()
    if SERVER_ADDRESS is None:
        queue_position = QUEUE.add_to_queue(QueueItem(user=chat.id, prompt=prompts, username=chat.username))
        await bot.send_message(chat_id=chat.id, text=f'Your prompt is added to the queue. Your current position is {queue_position}')
        return
    
    queue_position = QUEUE.determine_pos(QUEUE.find_queue_item_by_user(chat.id))
    if queue_position:
        await bot.send_message(chat_id=chat.id, text=f'Your prompt is in the queue. Your current position is {queue_position}')
        return
    SERVER_ADDRESS.busy(True)
    cfg['id'] = chat.id
    workflow = setup_workflow(prompts, cfg)


    async with aiohttp.ClientSession() as session:
        ws = await session.ws_connect(f"ws://{SERVER_ADDRESS.address()}/ws?clientId={client_id}")

        images = await get_images(ws, workflow, SERVER_ADDRESS.address(), session)
        videos = await get_video(ws, workflow, SERVER_ADDRESS.address(), session)

    for node_id in videos:
        for video_data in videos[node_id]:
            video = video_data

            try:
                await bot.send_video(chat_id=chat.id, video=video, supports_streaming=True)

                user_config = read_config(chat.id, chat.username)
                user_config['tokens'] -= VIDEO_PRICE
                update_config(chat.id, chat.username, user_config)

            except:
                log.error("Error sending video")

    SERVER_ADDRESS.busy(False)
    QUEUE.advance_queue()

    await notify_of_queue_change()
    await ws.close()



@bot.message_handler(content_types=['new_chat_members'])
async def bot_func(message):
    
    new = message.from_user.id
    print(f'Новый пользователь: {new}')
    whitelist.append(new)


@bot.message_handler(commands=['payment'])
async def send_payment_link(message):
    payments_db.connect()
    INV_ID = payments_db.get_last_inv_id()[0]

    signature = calculate_signature(
        MERCHANT_LOGIN,
        COST,
        INV_ID,
        MERCHANT_PASSWORD_1
    )
    data = generate_payment_data(merchant_login=MERCHANT_LOGIN, cost=COST, number=1, description=PAYMENT_DESC, signature=signature, is_test=1)
    markup = quick_markup({
        "Pay":{'web_app': WebAppInfo(generate_payment_link(data))}
    }, row_width=1)

    payments_db.connect()
    payments_db.add_payment(out_sum=COST, signature=signature, username=message.chat.username, user_id=message.chat.id)
    payments_db.close()

    await bot.send_message(chat_id=message.chat.id, text="You have to pay.", reply_markup=markup)

@bot.message_handler(commands=['help'])
@bot.message_handler(commands=['generate'])
async def start_message(message):
    add_config(message.chat)
    
    markup = quick_markup({
        # 'Text to Image': {'callback_data': 'txt2vid'},
        'Text to Video': {'callback_data': 'txt2vid'},
        # 'Image to Video': {'callback_data': 'img2vid'}
    }, row_width=2)

    # SERVERS = SERVER_ADDRESSES.servers()
    # 
    # for SERVER in SERVERS:
    #     queue_item = SERVER.get_queue().find_queue_item_by_user(message.chat.id)
    #     if queue_item:
    #         if SERVER.get_queue().determine_pos(queue_item) == 0:
    #             await bot.send_message(chat_id=message.chat.id, text="Be patient! AIDA is already hard at work bringing your masterpiece to life!")
    #         else:
    #             await bot.send_message(chat_id=message.chat.id, text="Be patient! AIDA has queued up your prompt and will begin work on it shortly. We'll notify you when that happens.")
    #         return

    await bot.send_message(chat_id=message.chat.id, text=START_TEXT, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('txt2vid'))    
async def callback_worker_text_to_image(call):
    await bot.set_state(call.message.chat.id, BotStates.text_aspect_ratio)
    markup = quick_markup({
        '1:1': {'callback_data': 'txt512x512'},
        # 'Portrait (2:3)': {'callback_data': 'txt512x768'},
        # 'Landscape (3:2)': {'callback_data': 'txt768x512'}
    }, row_width=2)

    await bot.send_message(chat_id=call.message.chat.id, text=CHOOSE_ASPECT_RATIO, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('img2vid'))    
async def callback_worker_image_to_video(call):
    await bot.set_state(call.message.chat.id, BotStates.video_aspect_ratio)
    markup = quick_markup({
        '1:1': {'callback_data': 'vid512x512'},
        # 'Portrait (2:3)': {'callback_data': 'vid512x768'},
        # 'Landscape (3:2)': {'callback_data': 'vid768x512'}
    }, row_width=2)
    await bot.send_message(chat_id=call.message.chat.id, text=CHOOSE_ASPECT_RATIO, reply_markup=markup)


@bot.callback_query_handler(state=BotStates.text_aspect_ratio, func=lambda call: call.data.startswith('txt'))
async def message_reply(call):
    await bot.set_state(call.message.chat.id, BotStates.generate)
    ratio = call.data.strip('txt')
    aspect_ratios[call.message.chat.id] = ratio
    await bot.send_message(chat_id=call.message.chat.id, text=HELP_TEXT)


@bot.callback_query_handler(state=BotStates.video_aspect_ratio, func=lambda call: call.data.startswith('vid'))
async def message_reply(call):
    await bot.set_state(call.message.chat.id, BotStates.generate)
    ratio = call.data.strip('txt')
    aspect_ratios[call.message.chat.id] = ratio
    await bot.send_message(chat_id=call.message.chat.id, text=IMAGE_TO_VIDEO_TEXT)

    # if ('/me' in prompt):
    #     w = re.findall('\\d+\\.?\\d*', prompt)
    #     if w:
    #         weight = w[0]
    #     else:
    #         weight = "1.0"

    #     fn = os.getcwd() + "/upload/face_" + str(message.chat.id) + "_" + str(cmt()) + ".png"
    #     with open(fn, 'wb') as new_file:
    #         new_file.write(imgf)
    #     chat_face[message.chat.id] = {'file' : fn, 'weight' : weight}
    #     log.info("FACE:%s (%s %s)", message.chat.id, message.chat.first_name, message.chat.username)
    #     with open('chat_face.pkl', 'wb') as f:
    #         pickle.dump(chat_face, f)
    #     await bot.send_message(chat_id=message.chat.id, text='Face image set. Use /face x.xx to set weight (0.5 for example)')
    #     return

    # if ('/style' in prompt):
    #     w = re.findall('\\d+\\.?\\d*', prompt)
    #     if w:
    #         weight = w[0]
    #     else:
    #         weight = "1.0"
    #     fn = os.getcwd() + "/upload/style_" + str(message.chat.id) + "_" + str(cmt()) + ".png"
    #     with open(fn, 'wb') as new_file:
    #         new_file.write(imgf)    
    #     chat_style[message.chat.id] = {'file' : fn, 'weight' : weight}
    #     log.info("STYLE:%s (%s %s)", message.chat.id, message.chat.first_name, message.chat.username)
    #     with open('chat_style.pkl', 'wb') as f:
    #         pickle.dump(chat_style, f)
    #     await bot.send_message(chat_id=message.chat.id, text='Style image set. Use /style x.xx to set weight (0.5 for example)')
    #     return

    


@bot.message_handler(state=BotStates.generate, content_types=['text'])
async def message_reply(message):
    await bot.delete_state(message.from_user.id, message.chat.id)
    
    for word in message.text.split():
        if word in filtered_words:
            await bot.send_message(chat_id=message.chat.id, text='Vulgar language is unacceptable.')
            return

    prompt = message.text 
    if message.from_user.id in aspect_ratios.keys():
        prompt+= aspect_ratios[message.from_user.id]
        aspect_ratios.pop(message.from_user.id)
    cfg = {}

    log.info("T2I:%s (%s %s) '%s'", message.chat.id, message.chat.first_name, message.chat.username, message.text)

    await comfy(message.chat, message.text, cfg)


@bot.message_handler(state=BotStates.generate, content_types=['photo'])
async def message_reply(message):
    await bot.delete_state(message.from_user.id, message.chat.id)
    prompt = ''
    if message.from_user.id in aspect_ratios.keys():
        prompt = aspect_ratios[message.from_user.id]
        aspect_ratios.pop(message.from_user.id)

    cfg = {}
    
    img_id = message.photo[len(message.photo)-1].file_id
    tmp = (await bot.get_file(img_id))
    imgf = (await bot.download_file(tmp.file_path))

    fn = os.getcwd() + "/upload/source_" + str(message.chat.id) + "_" + str(cmt()) + ".png"
    cfg['source_image'] = fn

    with open(fn, 'wb') as new_file:
        new_file.write(imgf)    

    log.info("I2I:%s (%s %s) '%s'", message.chat.id, message.chat.first_name, message.chat.username, message.caption)

    await comfy(message.chat, prompt, cfg)
    

log.info("Starting bot")

if __name__ == '__main__':
    bot.add_custom_filter(asyncio_filters.StateFilter(bot))
    asyncio.run(bot.infinity_polling())

# @bot.message_handler(commands=['models'])
# async def start_message(message):
#     md = 'Use @model_name\n'
#     for m in models:
#         md = md + m['name'] + "\n"
#     await bot.send_message(chat_id=message.chat.id, text=md)


# @bot.message_handler(commands=['loras'])
# async def start_message(message):
#     ld = 'Use @lora_name or @lora_name:strength\n'
#     for l in loras:
#         ld = ld + l['name'] + "\n"
#     await bot.send_message(chat_id=message.chat.id, text=ld)



# @bot.message_handler(commands=['me'])
# async def start_message(message):
#     w = re.findall('\\d+\\.?\\d*', message.text)
#     if w:
#         chat_face[message.chat.id]['weight'] = w[0]
#         await bot.send_message(chat_id=message.chat.id, text='Set face weight')
#     else:
#         del chat_face[message.chat.id]
#         await bot.send_message(chat_id=message.chat.id, text='Face cleared')


# @bot.message_handler(commands=['style'])
# async def start_message(message):
#     w = re.findall('\\d+\\.?\\d*', message.text)
#     if w:
#         chat_style[message.chat.id]['weight'] = w[0]
#         await bot.send_message(chat_id=message.chat.id, text='Set style weight')
#     else:
#         del chat_style[message.chat.id]
#         await bot.send_message(chat_id=message.chat.id, text='Style cleared')
