#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import logging
import spidev as SPI
import json

# =========================
# CONFIG
# =========================
DATA_PATH = "data.json"
LIB_PATH = "/home/axolotl/LCD_Module_code/LCD_Module_RPI_code/RaspberryPi/python"
FONT_PATH = "/home/axolotl/LCD_Module_code/LCD_Module_RPI_code/RaspberryPi/python/Font/Font01.ttf"

# Voeg lib pad toe
sys.path.append(LIB_PATH)

from lib import LCD_2inch4
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.DEBUG)

# =========================
# FUNCTIES
# =========================
def load_data(path=DATA_PATH):
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


def get_colors(kleur):
    kleur_map = {
        "red": (255, 0, 0),
        "orange": (255, 165, 0),
        "green": (0, 255, 0)
    }

    achtergrond = kleur_map.get(kleur.lower(), (255, 0, 0))

    if kleur.lower() == "green":
        tekst_kleur = "BLACK"
    else:
        tekst_kleur = "WHITE"

    return achtergrond, tekst_kleur


def main():
    try:
        # Data laden
        data = load_data(DATA_PATH)
        kleur = data.get('result', 'red')
        tekst = data.get('text', data.get('advice', ''))

        achtergrond, tekst_kleur = get_colors(kleur)

        # Display init
        disp = LCD_2inch4.LCD_2inch4()
        disp.Init()
        disp.clear()

        # Image maken
        image = Image.new("RGB", (disp.width, disp.height), achtergrond)
        draw = ImageDraw.Draw(image)

        # Font laden
        font = ImageFont.truetype(FONT_PATH, 24)

        # Tekst centreren
        bbox = draw.multiline_textbbox((0, 0), tekst, font=font, align="center")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (disp.width - text_width) // 2
        y = (disp.height - text_height) // 2

        # Tekst tekenen
        draw.multiline_text((x, y), tekst, fill=tekst_kleur, font=font, align="center")

        # Toon op scherm
        disp.ShowImage(image)

        # Blijf draaien
        while True:
            time.sleep(1)

    except IOError as e:
        logging.info(e)

    except KeyboardInterrupt:
        disp.module_exit()
        logging.info("quit:")
        exit()


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()