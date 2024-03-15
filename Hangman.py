#Import streamlit
#Rename session_state for readability
import streamlit as st
from streamlit import session_state as ss

#Import httpx to use API's for random word and dictionary
import httpx

# Import OpenAI API and set as client
from openai import OpenAI
client = OpenAI()

#Generate random word for the game from API and get its definition
def generate_random_word(length) -> str:
    #URL for random word API, if length = 'Random' an error will occur and API will generate a word with a random length
    try: 
        url_random_word_api = f"https://random-word-api.herokuapp.com/word?length={int(length)}"
    except:
       url_random_word_api = 'https://random-word-api.herokuapp.com/word'

    #empty list for returning all the lines in the word definition
    lines = []

    #loop while word not found
    while True:
        #Get random word from API
        with httpx.Client() as client:
            response = client.get(url_random_word_api)
            try:
                results = response.json() #set word in a list with the len of 1.
                    
            except Exception:
                results[0] = 'XXXXX'

        #Restart loop to try and get another word if exception.
        if results[0] == 'XXXXX':
            continue 
        
        #Url for dictionary API
        url_dictionary_api = f"https://api.dictionaryapi.dev/api/v2/entries/en/{results[0]}"

        #Get dictionary page for random word from dictionary API
        with httpx.Client() as client:
            response = client.get(url_dictionary_api)
            try:
                word_def = response.json()
                    
            except Exception:
                word_def = 'XXXXX'
        
        #If is a dict (or exception) then word not in dictionary (or failed), so restart loop to try again
        if word_def == 'XXXXX' or isinstance(word_def, dict):
            continue
        #if list, a result has been retrieved from dictionary API
        elif isinstance(word_def, list):
            #add results from dictionary to lines to generate the definition as a list
            for result in word_def:
                lines.append("-----------------------------------------------------------")
                lines.append(f"{result['word']}".title())
                lines.append("-----------------------------------------------------------")
                for meaning in result.get("meanings", []):
                    lines.append(f"*{meaning['partOfSpeech']}*\n")
                    lines.append("")
                    for definition in meaning.get("definitions", []):
                        lines.append(f" - {definition['definition']}\n")
        
        #turn definition list (lines) into a string then break the loop
        long_def = "\n".join(lines)
        break
     
    #return the random word and the definition
    return results[0].upper(), long_def

#function to validate input by determining if word in is the dictionary API. 
#The API returns a dict if no definition found and a list if definition is found and word in the dictionary.
def is_in_dictionary(value: str) -> bool:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{value}"

    with httpx.Client() as client:
        response = client.get(url)
        try:
            results = response.json()
              
        except Exception:
            results= 'XXXXX'
  
    if results == 'XXXXX' or isinstance(results, dict):
        return False
    elif isinstance(results, list):
        return True

#Function to store the text_input (user guess) and then clear the text_input for the next guess to save the user having to delete it.
def clear_text() -> None:
    ss.guess = ss.input
    ss.input = ''

#Function that is called when the user wins either by guessing the whole word or completing it by guessing letters
def winner() -> None:
    #Display balloons
    st.balloons()
    #Winner success message
    st.success(f'Congratulations on guessing {ss.random_word.upper()}! You saved the hanging man!', icon='🎈')
    st.title(ss.output)
    #Display definition of the word
    with st.expander('🤔 - See definition?'):
        st.write(ss.random_word_definition)
    #Image of winning man
    st.image('./images/winner-hangman.jpg', caption='Thank you ☺️')
    #Change game state to true to hide certain aspects from the screen
    ss.game_state = True
    #Play again button, resets ss variables and gets a new random word
    st.button('Fancy another round Champ?', key='play_again_champ', help='Play again?', type='primary')

#Function that is called when the user loses the game
def loser() -> None:
    #Loser failure messgae
    st.error(f'You failed to guess {ss.random_word.upper()}! You killed the man!', icon='💀')
    st.title(ss.output)
    #Display definition of the word
    with st.expander('🤔 - See definition?'):
        st.write(ss.random_word_definition)
    #Image of hanging man
    st.image('./images/0-hangman.jpg', caption='...uurgh..uuu..u..')
    #Change game state to true to hide certain aspects from the screen
    ss.game_state = True
    #Play again button, resets ss variables and gets a new random word
    st.button('Wanna kill again?', key='play_again_loser', help='Play again?', type='primary')

def ai_hint_display() -> None:
    with st.expander('Need help? Get a hint from AI'):
        if ss.openai_api_key.startswith('sk-') and len(ss.openai_api_key) > 40:
            ask_for_hint = st.button('Spend a life and ask AI for a hint', key='request_ai_hint', type='primary', )
            if ask_for_hint:
                with st.spinner(text="Thinking of a hint ..."):
                    get_ai_hint()
                if len(ss.previous_hints) > 1:
                    old_hints = '\n\n'.join(ss.previous_hints[:len(ss.previous_hints)-1])
                    st.markdown('*Previous hints:*')
                    st.write(old_hints)
            elif len(ss.previous_hints) > 0:
                old_hints = '\n\n'.join(ss.previous_hints)
                st.markdown('*Previous hints:*')
                st.write(old_hints)

        elif not ss.ai_hints:
            st.error('Please enable AI hints in the sidebar and enter your OpenAI API :key:', icon='👈')
        else:    
            st.info('Please enter your OpenAI API :key: in the box in the sidebar')

def get_ai_hint() -> None:
    ss.num_guesses += 1
    prompt = f"""A person is playing a game of hangman. The hangman word is '{ss.random_word}'. 
    They have guessed the following letters so far: {ss.previous_letters}. 
    Please provide a creative clue and/or hint to help them guess '{ss.random_word}'. 
    Please do not mention '{ss.random_word}' in your hint or clue and do not include its derivations in the hint or clue. 
    Please only return the clue or hint and nothing else. 
    Please do not make your hint or clue too obvious.
    You can make the hint or clue cryptic or challenging where appropriate.
    Your hint or clue may come in the form of a riddle or puzzle.
    When the word is a noun you may give a hint or clue where it is likely to be found, used, exist, etc..
    When the word is a verb you may give a hint or clue as to what the action entails or who or what might do the action.
    When the adjective is a verb you may give a hint or clue as to what it typically describes and how it describes it.
    Be very creative with your clues."""

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
        {"role": "system", "content": "You are a helpful assistant. You are very skilled and very creative at giving clues or hints to help humans solve word games and puzzles such as hangman."},
        {"role": "user", "content": prompt}
        ],
        temperature=0.9
    )
    hint = '🔎 - ' + completion.choices[0].message.content
    st.info(hint)
    ss.previous_hints.append(hint)

#Page settings including tab title and icon
st.set_page_config(page_title='Hangman', page_icon='🪢', layout='centered', initial_sidebar_state='auto')

#Streamlit sidebar
with st.sidebar:
    #Play again button, resets ss variables and gets a new random word
    new_game_button = st.button('Start new game', key='play_hangman', type="primary")
    st.divider()
    #List of basic rules of hangman
    st.caption('Basic rules')
    st.write('1. Press "Start new game" 🎮 \n 2. Guess a letter and hit enter ⌨️ \n 3. Keep guessing the letters 🧠 \n 4. Save the man from hanging by guessing the word :knot:')
    st.divider()
    #Game settings that can be changed
    st.markdown("### ⚙️ Settings")
    st.caption('Press start new game button for settings to take affect')
    #AI hints to be implemented
    st.caption('AI Hints')
    select_hints = st.checkbox('Enable AI hints?', key='ai_hints')
    if select_hints:
        st.info('🤖 To enable AI hints please enter your OpenAI API :key: below')
    openai_api_key = st.text_input(':key: OpenAI API Key', key='openai_api_key', type='password', disabled=not ss.ai_hints)
    #Change the length of the hangman word via a selectbox to accomodate the string 'Random' being the default choice
    select_word_length = st.selectbox(label='Select word length', options=['Random',4,5,6,7,8,9,10,11,12,13,14], index=0)
    #Allows user to change number of lives
    select_lives = st.slider('Select no. of lives', 4, 13, 7)
    #Disabled user from being able to guess vowels
    select_vowels = st.radio('Allow vowels to be guessed?', ['Yes', 'No'], horizontal=True)


# Check if one of the play again buttons has been pressed and that all of the session_state variables are initialised
#Also "resets" all of the ss variables and generates a new random word.
if (new_game_button or
    ss.get('play_again_champ') or
    ss.get('play_again_loser') or
    'random_word' not in ss or 
    'output' not in ss or 
    'lives' not in ss or 
    'num_guesses' not in ss or
    'input' not in ss or
    'guess' not in ss or
    'game_state' not in ss or
    'correct_letters' not in ss or
    'previous_letters' not in ss or
    'previous_hints' not in ss):
    #Generate random word from API
    ss.random_word, ss.random_word_definition = generate_random_word(select_word_length)
    #Generate the display _ _ _ _ with a length equal to the random word
    ss.output = ''.join([' _' for i in range(len(ss.random_word))])
    #Set lives equal to the number decided in the settings
    ss.lives = select_lives
    #Reset the text input and game variables used to track the progress of each game
    ss.num_guesses = 0
    ss.input = ''
    ss.guess = ''
    ss.game_state = False
    ss.correct_letters = 0
    ss.previous_letters = []
    ss.previous_hints = []

#Page title to be display above the game
st.title('🪢:skull: Hangman ', help='A game of skill and/or luck')

#Main input for user to submit their guesses for both letters and words. Label appears above the textbox.  
st.text_input(label='Type the letter or word to guess and hit enter', value='',key='input', on_change=clear_text, placeholder='Type here')

if ss.guess:
#Display an error is user enters anything but letters
    if not ss.guess.isalpha():
        st.error('Your guess must be a letter (A to Z) and no numbers or special characters', icon="🔤")

    #Display an error is user enters more than one letter or does not make a guess with the same number of letters as the hangman word
    elif not ((len(ss.guess) == 1) or (len(ss.guess) == len(ss.random_word))):
        st.error(f'Your guess must be either a letter or {len(ss.random_word)} letters long to match the hangman word.', icon="🔢")
    
    #If player guesses a single letter, test to see if it ...
    #...has already been guessed before, thereby prevent repeat inputs
    #...is a vowel and guessing vowels are forbidden by the settings 
    #...is not in the word, and check if last life and end the game or
    #display message that letter is not in word. 
    #After each guess add to it a list to be displayed and prevent a repeat entries
    elif len(ss.guess) == 1:
        
        if ss.guess.upper() in ss.previous_letters:
            st.error(f'You have already guessed the letter {ss.guess.upper()}!', icon='😳')
        
        elif select_vowels == 'No' and ss.guess.upper() in 'AEIOU':
            st.error(f'You are not allowed to guess vowels!', icon='😡')

        elif ss.guess.upper() not in ss.random_word.upper():
            ss.num_guesses += 1
            if ss.num_guesses >= ss.lives:
                loser()
            else:
                st.warning(f'Unlucky the letter {ss.guess.upper()} is not the word!', icon='😢')
            
            ss.previous_letters.append(ss.guess.upper())
        #..is in the word. If so ... , 
        elif ss.guess.upper()  in ss.random_word.upper():
           
            
            #...add to list of previous guesses
            ss.previous_letters.append(ss.guess.upper())
            #...make a list of all the indexes(+1) that the letter is at 
            positions = [pos+1 for pos, char in enumerate(ss.random_word) if char == ss.guess.upper()]
            #Initialise temp_output as strings are inmutable 
            temp_output = ''
            #For each index, change the display e.g. for L and HELLO change _ _ _ _ _ to _ _ L L _ and 
            #increase the count of correct characters by one for each position, e.g. from 0 to 2 for our L and HELLO exampl
            for position in positions:
                temp_output = ss.output[:position*2-1] + ss.guess.upper() + ss.output[position*2:]
                ss.output = temp_output
                ss.correct_letters += 1
    
            #Check if user has won the game by guessing individual letters, check after each correct guess, and display winning message and end the game
            #...else display success message
            if ss.correct_letters == len(ss.random_word):
                winner()
            else:
                st.info(f'Well done {ss.guess.upper()} is in the word', icon='✅')
    #If player has guessed a word equal in length to the hangman word (i.e. tried to guess the word)
    elif len(ss.guess) == len(ss.random_word):
        #If guess is not in the dictionary, give them a free pass
        if not is_in_dictionary(ss.guess):
            st.error(f'Your guess is not in our dictionary!', icon="📚")
        #If guess not the word, lose a life, check if the player has lost, if so, end game, if not display a warning
        elif not ss.guess.upper() == ss.random_word.upper():
            ss.num_guesses += 1
            if ss.num_guesses >= ss.lives:
                loser()
            else:
                st.warning(f'Unlucky the word is not {ss.guess}!', icon='😢')

        #If guess is the word, end game and display winning message
        elif ss.guess.upper() == ss.random_word.upper():
            winner()
else:
    #Display instructions at the start of the game
    st.info('Sidebar contains ℹ️ on how to play, settings ⚙️ and how to enable AI hints 🤖', icon="⬅️")

#If game being play, display the game
if not ss.game_state:
    ai_hint_display()
    #Display the game _ _ L L _
    st.title(ss.output)
    #Display the prevously guessed letters
    if len(ss.previous_letters) > 0:
        already = '*Already guessed:* \n'
        previous = sorted(ss.previous_letters)
        previous_str = ', '.join(previous)
        st.markdown(already + previous_str)

    #Display the hangman image
    st.image(f'./images/{13 - ss.num_guesses}-hangman.jpg', caption=f'Lives remaining:{ss.lives - ss.num_guesses}')