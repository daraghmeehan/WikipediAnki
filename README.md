# WikipediAnki

Accumulating encyclopaedic knowledge with Anki

## Inspiration

A year or two ago, I found a paper where the authors created the [Wikiflash tool](https://tik-db.ee.ethz.ch/file/130cdc2003615c74c07f9830158ee345/Flashcards_AAAI_21_AIEd_CameraReady.pdf) which generate flashcards from Wikipedia articles automatically.

Apart from it not being available to use, the decks of flashcards it created were mediocre at best - they contained a lot of either basic facts that nearly everyone knows, or very specific information that is not of much use to learn.

My goal is creating a tool which allows a user to read Wikipedia by themselves, and be able to quickly extract information to create custom flashcards for learning about any topic.

The diagram below shows 11 potential flashcards to be extracted from the page of Émile Zola. 

<img width="2502" alt="WA poster" src="https://github.com/daraghmeehan/WikipediAnki/assets/47535504/ef892b7c-eba5-497f-98f6-ef4d08c3e17e">


The diagram below shows some examples of my use of [this]([url](https://ankiweb.net/shared/info/1374772155)) image occlusion tool.

<img width="1213" alt="WA occlusion" src="https://github.com/daraghmeehan/WikipediAnki/assets/47535504/e751eee2-7a98-4739-a1e6-3023d675d57b">



## Scope of current version of the tool

The program I have developed is to be run at the same time as browsing a Wikipedia page. Upon starting the program the user is asked which Wikipedia page they would like to make flashcards for.

Next, the program breaks down the page using BeautifulSoup, a well-known package for web scraping, and a SpaCy language model of the English language for sentence splitting and tokenisation. The user interacts with the program by typing a substring of the sentence they wish to create a flashcard for - then they are shown the list of matching sentences.

The user selects their sentence and are then shown the list of words of the sentence. They can choose to omit several spans of the sentence which then form the answer, or instead use the title of the page as the answer.

Example span answer:
Q - Earth's liquid outer core generates the magnetic field that shapes Earth's [1], deflecting destructive [2] [2].
A - [1] magnetosphere, [2] solar winds

Example title answer:
Q - The club's traditional kit consists of red shirts, white shorts and red socks, and their most commonly used nickname is The Addicks.
A - Charlton Athletic

When the user is finished creating cards for an individual page, then can go back and select a different page to continue learning, or exit. After they have finished the program saves the created flashcards to a folder with csv files, which can easily be imported in the Anki desktop app.

## Future development

In future there are many features I would like to add.

- the ability to save articles in various folders (e.g. finished studying, in progress, to read).
- visualisation of your exploration of Wikipedia (for example different categories) and connections between pages you have studied, and statistics on types of pages looked at and days studied.
- tracking progress on sections of individual pages/collections of pages.
- suggesting other pages to read.
- checking for updates in pages which may render facts inaccurate/out of date.
- adding more information to each card created, e.g. paragraph number/section of the page.
- perhaps linking cards to where they are located in Wikipedia.
- allow the use of more languages (e.g. using Wikipedia in Spanish) -> this means we would use a different SpaCy model which is an easy thing to swap out
- it would be nice to be able to see flashcards created in current session.
- the usage of knowledge graphs can also be envisioned to link a user to adjacent topics for an automatically generated curriculum.

My version is still fallible to bad sentence separation from SpaCy, and it highlights one particular weakness - only one sentence can be used in the question at a time, and user editing of the fields is thus quite slow if there is a lot to change with a card.

Extra Note: The function edit_fields() is ugly but robust - I was trying to hard to make this short and kept getting errors.

## How to run project

First the required packages must be installed, available in requirements.txt. Using a virtual environment is advised.

Next simply run "python version_1.py" and follow the dialogue.

The final flashcard collection is output to "./Flashcards/{current_date_and_time} - {number of flashcards} cards.csv".

## Sample Dialogue

    Welcome to WikipediAnki!

    What Wikipedia page do you want to learn from? Or input "b" to quit and save flashcards.
    https://en.wikipedia.org/wiki/Earth
    You have chosen the page "Earth"

    Type a substring of the sentence you want to make a flashcard for.
    Enter "b" to cancel.
    densest
    Choose which line to learn from, or go back with "b".
    1) It is the densest planet in the Solar System.

    Which line do you want to learn? Or go back with "b".
    1

    Please choose from the words of the sentence.
    1 It
    2 is
    3 the
    4 densest
    5 planet
    6 in
    7 the
    8 Solar
    9 System
    10 .

    Select a span (e.g. "[1,2,3]"), a single word (e.g. "[5]"), or even a multiple spans (e.g. "[[1,2], [5,6]]")
    Enter "t" to use the page's title as the answer.
    Enter "b" to cancel.
    [4]

    This is what your flashcard will look like:

    Question:
    It is the [1] planet in the Solar System.
    ----------
    Answer:
    1 densest

    Do you want to add a hint?
    [y/n] y

    Please type your hint. Use "\n" to create multiple line hints for multiple spans.
    Enter "b" to cancel.
    mass

    This is what your flashcard will look like:

    Question:
    It is the [1] planet in the Solar System.
    Hint:
    mass
    ----------
    Answer:
    1 densest

    Finally, would you like to edit any field?
    [y/n] n

    Successfully created card.


    Type a substring of the sentence you want to make a flashcard for.
    Enter "b" to cancel.
    b
    Are you sure you want to stop making new cards?
    [y/n] y

    Would you like to choose another page?
    [y/n] n

    Finished studying. Saving flashcards to .csv

## Sample Output File

Below is the .csv for the above example.

    It is the [1] planet in the Solar System.,1 densest,mass,Earth,https://en.wikipedia.org/wiki/Earth

## What one flashcard looks like in Anki

Front:

    It is the [1] planet in the Solar System.
    Hint: mass
    -----
    ?

Back:

    It is the [1] planet in the Solar System.
    From 'Earth'
    -----
    1 densest
