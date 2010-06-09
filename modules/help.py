# -*- coding: utf-8 -*-
topics = {
  "defind"   :"Identify the correct definition among all given suggestions. Commands: .defind .def .select",
  "food"     :"Food is important, when you spend your time in the channels. Commands: food",
  "hangman"  :"Guess words, one notch at a time. Commands: .hang .hreset .buy .htop .bought",
  "history"  :"A multiplayer game. Order historical dates on a timeline. More: hrules Commands: .history .hrun .card .cards .call .hquit",
  "jumble"   :"Descramble English words. Commands: .jumble .jtop",
  "roulette" :"Play Russian roulette. Commands: .load .spin .die",
  "taboo"    :"Describe words without using taboo words. Commands: .taboo .pass .ttop",
  "trivia"   :"Trivia with random pages from Wikipedia. Commands: .trivia .stop .solve .mode .source .score .top .report",  
  "words"    :"Find words in a grid of letters. Commands: .words .wtop",
  "lookup"   :"You can look up words using the commands: .wiki .dict .encarta .wordnet .check",
  "three"    :"Find words containing given consonants: .three .3top .3reset",
  "bend"     :"Find words beginning and ending with the given letters: .bend .btop .breset",
  "bank"     :"Find the longest word in the power set of the given letters: .bank .banktop .sbank",
  "tags"     :"Assign (matching or non-matching) adjectives to topics that others propose: trules .tags .trun .tquit .discuss .that's .tag .pass",
}
commands = {
  ".hang"    :"Start a game of hangman",
  ".hreset"  :"Reset the current game of hangman",
  ".buy"     :"Buy a hangman letter. But beware, you may buy it with your life.",
  ".bought"  :"Display the already bought letters.",
  ".htop"    :"Show the current hangman highscore list.",
  ".tags"    :"Join a game of .tags",
  ".trun"    :"Start a game of .tags with the current players",
  ".discuss" :"Propose a topic to propose cards about.",
  ".that's"  :"Play a card matching (OR NOT!) the currently proposed topic.",
  ".tquit"   :"Quit the current game of .tags",
  "trules"   :"You will be dealt adjectives and a rule. One player must announce a topic, then everyone plays an adjective according to his secret rule. In the second round, players must tag the cards they think match the topic by entering the displayed code. First come, first serve. Or .pass. Points are dealt for correct guesses, and correctly tagged cards.",
  ".tag"     :".tag code: Tag a card in a game of .tags",
  ".pass"    :"Do not tag any card in a game of .tags",
  ".three"   :"A sequence of 3-5 consonants. Find a word starting with these in order or reverse order. Syntax: .three #number where #number is the number of consonants to play with.",
  ".food"    :"Serves you a random sandwich. Real food is only served in real life.",
  "hrules"   :"Cards contain historical events. Players receive 8 cards. One card is dealt. Players take turns to add one card to the timeline, or 'call' if they believe the timeline is wrong. Two cards penalty for calling if the timeline is correct, or for the previous player if incorrect. Play all cards to win.",
  ".history" :"Joins the history game. The game may be starting up, or already running.",
  ".hrun"    :"Starts the history game.",
  ".hquit"   :"Leaves a running game.",
  ".call"    :"Verifies the correctness of the current timeline. 2 cards penalty for the previous player, if incorrect. Or for the caller if correct.",
  ".card"    :"Plays a card on the table. Keywords are 'first', 'last', 'before', 'after'. Syntax examples '.card #h first' or '.card #h before #t' where #h is card number on hand, #t is card number on table.",
  ".cards"   :"Resends a private message listing all cards currently on hand.",
  ".help"    :"The world has just imploded as it hit an infinite recursion. It was promptly replaced with a new, shiny one.",
  ".jumble"  :"Displays a new scrambled word, or the current one if unsolved. Type the correct word to solve.",
  ".jtop"    :"Displays the current high score list for jumble.",
  ".3top"    :"Displays the current high score list for three.",
  ".3reset"  :"Ends the current game of three.",
  ".bend"    :"Displays a new word to complete. Type your guess. After the last correct guess, you have 30 seconds to improve.",
  ".btop"    :"Display the high score list for bend",
  ".breset"  :"Solve the last bend puzzle.",
  ".bank"    :"Displays a new letter bank. Type your guess. After the last correct guess, you have 30 seconds to improve.",
  ".banktop" :"Display the high score list for bank",
  ".sbank"   :"Solve and end the current bank puzzle, or show the solution for the last puzzle.",
  ".load"    :"Loads a revolver. Parameters '.load #b #c' where #b is a number of bullets, #c a number of chambers in the cylinder.",
  ".spin"    :"Spins the cylinder to a random position.",
  ".die"     :"Pulls the trigger. You may die if a bullet is in the current chamber.",
  ".taboo"   :"You will receive definitions for five minutes. One point per guessed definition. The player who types the correct word(s) also scores one point.",
  ".pass"    :"If the current definition is too difficult, you may .pass",
  ".ttop"    :"Displays the high score table for taboo.",
  ".trivia"  :"'.trivia #q' starts a new game of trivia with #q questions. Default is 20. Type the correct answer to score.",
  ".stop"    :"Stops the current game of trivia. Meh.",
  ".solve"   :"Solves the current trivia question.",
  ".mode"    :"'.mode line' or '.mode paragraph' switches between displaying one line or the first paragraph of the definition.",
  ".source"  :"'.source list' or '.source random' switches between choosing random questions from a list or Special:Randompages at Wikipedia.",
  ".score"   :"Displays the trivia scores for the current or last active round.",
  ".top"     :"Displays the trivia high score table.",
  ".report"  :"Report the current trivia question as incorrect. May be abbreviated as '.r'. Any parameters are sent as comment for clarification.",
  ".words"   :"Displays a new, or current grid of letters. '.words #s' specifies the size as #s x #s grid. Type the longest word you can find to score points. Longer words bring more points, and even more with less guessing around.",
  ".wtop"    :"Displays the words high score table.",
  ".wiki"    :"Looks up a word using the wikipedia search function.",
  ".wordnet" :"Looks up a word in the wordnet set of dictionaries.",
  ".encarta" :"Looks up a word in the Encarta",
  ".dict"    :"Looks up a word in encarta and wordnet.",
  ".check"   :"Checks if a word is contained in the internal (YAWL) wordlist and on morewords.com",
  ".defind"  :"Starts a game of defind",
  ".def"     :"Submits a definition for the currently proposed word. Please do so via private message to the bot",
  ".select"  :"Selects the one definition which you consider to be correct.",
}

def help(phenny, input):
  words = input.split()
  if len(words)<2:
    phenny.say("There's help on several topics. .help topics shows a list. Display more help by indicating a topic or command.")
  else:
    topic = words[1]
    if topic == "topics":
      list = sorted(topics.keys())
      slist = reduce(lambda x,y:x+", "+y, list)
      phenny.say("There's help on "+slist)
    elif topic in topics:
      phenny.say(topics[topic])
    elif topic in commands:
      phenny.say(commands[topic])
    else:
      phenny.say("I can't help you with that. Some help pages are still missing.")
help.commands = ['help','man','usage']
help.priority = 'low'
help.thread = False

