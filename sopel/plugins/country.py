import json
import random
from pathlib import Path
from sopel import plugin
from sopel import formatting

def green_text(s):
  return formatting.color(str(s), formatting.colors.GREEN)

def blue_text(s):
  return formatting.color(str(s), formatting.colors.BLUE)  

def yellow_text(s):
  return formatting.color(str(s), formatting.colors.YELLOW)  

# Show the hint and flag image
def show_message(bot, trigger):
  hint = bot.db.get_channel_value(trigger.sender, "flags_hint")
  bot.say(f"Guess this country | {hint}")

# Show the answer
def show_answer(bot, trigger):
  name = bot.db.get_channel_value(trigger.sender, "flags_name")
  bot.say(f"The answer was: {name}")  

# Select a new country
def new_country(bot, trigger):
  # Load country info json (big)
  p = Path(__file__).parent.resolve()
  countries_file = open(p / Path("country_info.json"), "r")
  countries = json.load(countries_file)
  countries_file.close()

  # Choose a random coutnry
  country = random.choice(countries)

  # Choose which hint to show
  hint_number = random.randint(1, 5)
  hints = []

  if country["Capital"]:
    c = green_text("capital")
    s = country["Capital"]
    hints.append(f"The {c} is {s}")
  if country["Currency"]:
    c = green_text("currency")
    s = country["Currency"]
    hints.append(f"The {c} is {s}")
  if country["Languages"]:
    c = green_text("languages")
    s = country["Languages"]
    hints.append(f"The {c} are {s}")
  if country["Area KM2"]:
    c = green_text("area")
    s = country["Area KM2"]
    hints.append(f"The {c} is {s} km2")
  if country["Continent"]:
    c = green_text("continent")
    s = country["Continent"]
    hints.append(f"The {c} is {s}")

  hint = " | ".join(hints)
  
  # Save current country code in db
  bot.db.set_channel_value(trigger.sender, "flags_name", country["Country Name"])
  bot.db.set_channel_value(trigger.sender, "flags_hint", hint)

  # Show the message
  show_message(bot, trigger)  

@plugin.command("country")
def show_country(bot, trigger):
  if trigger.group(2):
    if trigger.group(2).strip().lower() == "skip":
      show_answer(bot, trigger)
      new_country(bot, trigger)
  else:
    show_message(bot, trigger)

@plugin.rule(".*")
def guess_country(bot, trigger):
  # If country selected try to guess or print message
  name = bot.db.get_channel_value(trigger.sender, "flags_name")

  if name:
    # If argument then try to guess
    line = trigger.group()
    if line:
      guess = line.strip().lower()
      if name.lower() in guess:
        c = green_text(f"{name} is correct!")
        bot.say(c)
        new_country(bot, trigger)
  else:
    new_country(bot, trigger)
