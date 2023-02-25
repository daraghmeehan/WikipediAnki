import requests, spacy
from bs4 import BeautifulSoup

import pandas as pd  # for collecting our flashcards
import re  # for cleaning Wikipedia text
import ast  # for converting string representation of list to a list
import pyperclip  # for editing flashcards quickly by copying to the clipboard
import time  # for timestamping csv of flashcards
from pathlib import Path  # for writing flashcards to "Flashcards" folder

nlp = spacy.load("en_core_web_sm")  # loading the language model


def run_wikipedianki() -> None:
    """Runs the WikipediAnki program."""

    print("\nWelcome to WikipediAnki!")

    flashcards = pd.DataFrame(
        columns=["Question", "Answer", "Hint", "Extra Info", "is_easy", "Title", "URL"]
    )

    try:
        while True:

            next_action = choose_next_action()

            # study a new page
            if next_action == "s":
                # choose page
                wikipedia_url, soup = choose_page()
                if wikipedia_url == "b":
                    continue

                new_cards = create_new_cards(wikipedia_url, soup)

                flashcards = pd.concat([flashcards, new_cards], ignore_index=True)

                print("\nYour new cards have been saved.")

            # make custom card
            elif next_action == "c":
                custom_card = make_custom_card()

                custom_card = pd.DataFrame(custom_card)

                # add the new flashcard to our collection
                flashcards = pd.concat([flashcards, custom_card], ignore_index=True)

            # edit current cards
            elif next_action == "e":
                flashcards = edit_flashcards(flashcards)
                pass

            # exit and save
            elif next_action == "b":
                # exit condition
                break

    except:
        print("Error encountered. Saving current flashcards and exiting...")

    # save to file
    print("\nFinished studying. Saving flashcards to .csv\n")
    save_flashcards_to_csv(flashcards)


def choose_next_action():
    """Asks the user if they would like to study a page, edit current flashcards, or exit"""
    next_action = input(
        "What would you like to do?\nType 's' to study a page, 'c' to make a custom card, 'e' to edit created flashcards, 'b' to exit and save.\n"
    )

    if next_action in ["s", "c", "e", "b"]:
        return next_action
    else:
        return choose_next_action()


def choose_page() -> tuple[str, BeautifulSoup]:
    """Asks the user what Wikipedia page to learn from, and returns the final URL and BeautifulSoup's soup object of the page."""

    wikipedia_url = input(
        '\nWhat Wikipedia page do you want to learn from? Or input "b" to quit and save flashcards.\n'
    )

    if wikipedia_url == "b":
        return wikipedia_url, None

    try:
        r = requests.get(wikipedia_url, allow_redirects=True)
        # use original encoding of content!! instead of utf-8
        soup = BeautifulSoup(r.content, "html.parser", from_encoding="utf-8")
        redirected_address = soup.find("link", rel="canonical").get("href")
        assert (
            wikipedia_url == redirected_address
        )  # if choose "Barack", we get redirected to "Barack Obama". Assert equal to make sure user has desired page, and using consistent naming of pages
    except:
        print(
            "Please try again with a valid Wikipedia page.\nThis includes the correct redirected address.\n"
        )
        return choose_page()

    return wikipedia_url, soup


def create_new_cards(wikipedia_url: str, soup: BeautifulSoup) -> pd.DataFrame:
    """The user creates new cards by studying the given Wikipedia page."""

    page_title = soup.find(id="firstHeading").text
    print(f'You have chosen the page "{page_title}"')

    # make cards
    new_cards = study_page(soup)

    # add extra page information to each card
    for card in new_cards:
        card["Title"] = page_title
        card["URL"] = wikipedia_url

    # add new cards to our collection
    new_cards = pd.DataFrame(new_cards)

    return new_cards


def study_page(soup: BeautifulSoup) -> list[dict[str, any]]:
    """Using a given page's soup object, creates new flashcards of user-selected sentences, and returns a list of the new cards to add to our deck."""

    page_title = soup.find(
        id="firstHeading"
    ).text  # in case want to use title as answer

    text = retrieve_text(soup)

    doc = nlp(text)  # doing sentence splitting and tokenisation
    sents = list(doc.sents)  # all sentences are type spacy.tokens.span.Span

    new_cards = []

    while True:

        try:
            next_card = create_next_card(sents, page_title)
        except:
            print("Error creating new cards. Saving current created cards.")
            next_card = {}

        if next_card == {}:
            return new_cards

        new_cards.append(next_card)


def retrieve_text(soup: BeautifulSoup) -> str:
    """Retrieves the text of the given page, with basic preprocessing."""

    all_paragraphs = soup.find_all(["p", "li"])
    text = "\n".join(
        [
            paragraph.text.strip()
            for paragraph in all_paragraphs
            if not re.match("/s*", paragraph.text)
        ]
    )  # first and last paragraphs are usually "\n"
    text = re.sub(
        r"(\[[0-9]+\])|(\[i+\])|(\[[a-z]\])", "", text
    )  # removing [1], [2] etc. from text

    return text


def create_next_card(
    sents: list[spacy.tokens.span.Span], page_title: str
) -> dict[str, any]:
    """Given sentences of Wikipedia page, creates new card from a user-selected sentence."""

    ##!! also need previous card editing
    ##!! maybe want to be able to exit at any time

    ##!! add custom card here
    sentence_substring = input(
        '\nType a substring of the sentence you want to make a flashcard for.\nEnter "b" to cancel.\n'
    )

    if sentence_substring == "b":
        return {}

    # simple way to find matching sentences
    matching_sents = [sent for sent in sents if sentence_substring in sent.text]

    if len(matching_sents) == 0:
        print("No matching sentences. Please try again.")
        return create_next_card(sents, page_title)

    if len(matching_sents) > 10:
        print(
            "More than 10 matching sentences. Please be more specific to narrow down your search."
        )
        return create_next_card(sents, page_title)

    line_number_to_learn = choose_line(matching_sents)
    if line_number_to_learn == -1:
        return create_next_card(sents, page_title)

    line_to_learn = matching_sents[line_number_to_learn - 1]

    next_card = create_card_from_line(line_to_learn, page_title)
    if next_card == {}:
        # if choose to not make a flashcard for this sentence, allow choosing a different sentence
        return create_next_card(sents, page_title)

    return next_card


def choose_line(sents: list[spacy.tokens.span.Span]) -> int:
    """Asks user which line they want to make a flashcard from of those that match the user's input."""

    print('\nChoose which line to learn from, or go back with "b".')

    for i in range(1, len(sents) + 1):
        print(f"{i}) {sents[i - 1]}")

    line_number_to_learn = input(
        '\nWhich line do you want to learn? Or go back with "b".\n'
    )

    if line_number_to_learn == "b":
        return -1
    else:
        try:
            line_number_to_learn = int(line_number_to_learn)
        except:
            line_number_to_learn = -1

    if 1 <= line_number_to_learn <= len(sents):
        return line_number_to_learn
    else:
        print("Please try again and choose a valid line.")
        return choose_line(sents)


def create_card_from_line(
    line_to_learn: spacy.tokens.span.Span, page_title: str
) -> dict[str, any]:
    """The user determines what the card for the given line will look like, and the completed card is returned."""

    print("\nPlease choose from the words of the sentence.")
    # printing words of line
    for i in range(1, len(line_to_learn) + 1):
        print(f"{i} {line_to_learn[i - 1]}")

    selected_spans_str = input(
        f'\nSelect a span (e.g. "[1,2,3]"), a single word (e.g. "[5]"), or even a multiple spans (e.g. "[[1,2], [5,6]]")\nEnter "t" to use the page\'s title as the answer.\nEnter "b" to cancel.\n'
    )

    if selected_spans_str == "b":
        return {}

    elif selected_spans_str == "t":
        # use the page's title as the answer
        question = line_to_learn.text
        answer = page_title

    else:
        # otherwise need to parse the given spans and build the question and answers to print on the flashcard
        try:
            selected_spans = parse_selected_subspans(selected_spans_str)
            question, all_answer_strings = extract_answers_from_line_to_learn(
                line_to_learn, selected_spans
            )
            answer = build_answer(all_answer_strings)
        except:
            print(
                "Cannot create a card with chosen spans. Please try again with a valid span selection."
            )
            return create_card_from_line(line_to_learn, page_title)

    print_card_preview(question, answer)

    hint = ""
    extra_info = ""

    question, answer, hint, extra_info = edit_fields(question, answer, hint, extra_info)

    card = {
        "Question": question,
        "Answer": answer,
        "Hint": hint,
        "Extra Info": extra_info,
    }

    card["is_easy"] = confirm_with_user("\nFinally, is this an easy card?")

    print("\nSuccessfully created card.\n")

    return card


def parse_selected_subspans(selected_spans_str: str) -> list[list[int]]:
    """Parses the user's inputted subspan selection, raising an error if not in the format expected."""

    selected_spans = ast.literal_eval(selected_spans_str)
    assert isinstance(selected_spans, list)

    if isinstance(selected_spans[0], int):
        # if only have one span, e.g. "[1,2,3]" or "[5]"
        selected_spans = [selected_spans]  # can trivially treat as a nested span

    elif not isinstance(selected_spans[0], list):
        raise

    return selected_spans


def extract_answers_from_line_to_learn(
    line_to_learn: spacy.tokens.span.Span, selected_spans: list[list[int]]
) -> tuple[str, list[str]]:
    """Extracts the answer substrings from our chosen line, returning the formatted question string and a list of the corresponding answers that were removed."""

    all_answer_positions = (
        []
    )  # to track all the token indices in the sentence to be removed
    span_numbers = (
        {}
    )  # to track, for a given index, which span group (i.e. the answer) it corresponds to
    answer_strings = []  # to collect the answers for the given subspans

    # reminder that selected_spans is a list of spans, e.g. [[1,2], [5,6]], or simply [[1,2,3]]
    all_answer_positions = [
        idx for sub_span in selected_spans for idx in sub_span
    ]  # simply extracting every index from our list of lists (which will tell us quickly if a given position is part of an answer or not)

    for sub_span_number, sub_span in enumerate(selected_spans, start=1):
        answer_string = ""

        for position_in_line in sub_span:
            span_numbers[
                position_in_line
            ] = sub_span_number  # assigns individual index in our line to a specific subspan (answer), to use when creating the flashcard

            # collecting parts of answer string for given subspan
            answer_string += line_to_learn[position_in_line - 1].text_with_ws

        answer_string = (
            answer_string.strip()
        )  # to remove trailing whitespace when we collected the parts of the string
        answer_strings.append(answer_string)

    question = build_question(line_to_learn, all_answer_positions, span_numbers)

    return question, answer_strings


def build_question(
    line_to_learn: spacy.tokens.span.Span,
    all_answer_positions: list[int],
    span_numbers: dict[int, int],
) -> str:
    """Builds the question side of the flashcard for our chosen line, replacing all token positions that form the question with their respective subspan number."""

    question = ""

    for i in range(1, len(line_to_learn) + 1):
        token = line_to_learn[i - 1]
        if i in all_answer_positions:
            span_number = span_numbers[i]  # like a reverse dict search
            question += f"[{span_number}]"
            question += token.whitespace_
        else:
            question += token.text_with_ws

    # cleaning up potential whitespace inconsistencies with bs4 and spacy
    question = question.strip()
    question = question.replace("  ", " ")
    return question


def build_answer(answers: list[str]) -> str:
    """Builds the answer side of the flashcard from a list of the individual subspan answers."""

    answer = "\n".join(
        f"{i} - {individual_answer}"
        for i, individual_answer in enumerate(answers, start=1)
    )

    # cleaning up potential whitespace inconsistencies with bs4 and spacy
    answer = answer.strip()
    answer = answer.replace("  ", " ")
    return answer


# def write_hint() -> str:
#     """The user writes what they would like their hint to be."""

#     hint = input('\nPlease type your hint. Use "\\n" to create multiple line hints for multiple spans.\nEnter "b" to cancel.\n')

#     if hint in ["", "b"]:
#         if confirm_with_user("\nWant to skip making a hint?"):
#             return ""
#         else:
#             return write_hint()
#     else:
#         return hint


def print_card_preview(question: str, answer: str, hint="", extra_info="") -> None:
    """Gives the user a preview of what their card will look like, so they can choose whether or not to make further changes."""

    print("\nThis is what your flashcard will look like:\n")
    print(f"Question:\n{question}")
    if hint != "":
        print(f"Hint:\n{hint}")
    print("----------")
    print(f"Answer:\n{answer}")
    if extra_info != "":
        print(f"Extra Info: {extra_info}")


def edit_fields(
    question: str, answer: str, hint: str, extra_info: str
) -> tuple[str, str, str, str]:
    """Allows the user to edit the fields of the flashcard in case they aren't happy, or add a hint or extra info if they haven't done so."""

    print(
        '\nNow editing fields. Enter "q" for question, "a" for answer, "h" for hint, "e" for extra info, "b" to stop editing.\nUse "\\n" to create multiple line fields (e.g. for hints for multiple spans).\n'
    )

    field = input("Which field would you like to edit?\n")

    # if confirm_with_user("\nDo you want to add a hint?"):
    #     hint = write_hint()
    #     hint = hint.replace("\\n", "\n")  # to handle multiple line hints
    #     print_card_preview(question, answer, hint)

    # Use "\\n" to create multiple line hints for multiple spans.

    if field not in ["q", "a", "h", "e", "b"]:
        return edit_fields(question, answer, hint, extra_info)

    elif field == "b":
        return question, answer, hint, extra_info

    elif field == "q":
        pyperclip.copy(question.replace("\n", "\\n"))
        # print(f"\nQuestion was: {question}, which has been copied to the clipboard.\n")
        new_question = input(
            'Enter "b" to cancel the operation. Replace question with:\n'
        )
        if new_question == "b":
            return edit_fields(question, answer, hint, extra_info)
        else:
            question = new_question
            question = question.replace("\\n", "\n")  # to handle added new lines

    elif field == "a":
        pyperclip.copy(
            answer.replace("\n", "\\n")
        )  # so when copy we get \n pasting in command line
        # print(f"\nAnswer was: {answer}, which has been copied to the clipboard.\n")
        new_answer = input('Enter "b" to cancel the operation. Replace answer with:\n')
        if new_answer == "b":
            return edit_fields(question, answer, hint, extra_info)
        else:
            answer = new_answer
            answer = answer.replace("\\n", "\n")  # to handle added new lines

    elif field == "h":
        pyperclip.copy(hint.replace("\n", "\\n"))

        if hint == "":
            print(f"\nCreating a hint.\n")
            new_hint = input('Enter "b" to cancel the operation. New hint:\n')
        else:
            # print(f"\nHint was: {hint}, which has been copied to the clipboard.\n")
            new_hint = input('Enter "b" to cancel the operation. Replace hint with:\n')
        if new_hint == "b":
            return edit_fields(question, answer, hint, extra_info)
        else:
            hint = new_hint
            hint = hint.replace("\\n", "\n")  # to handle added new lines

    elif field == "e":
        pyperclip.copy(extra_info.replace("\n", "\\n"))
        if extra_info == "":
            print(f"\nCreating extra info.\n")
            new_extra_info = input(
                'Enter "b" to cancel the operation. New extra info:\n'
            )
        else:
            print(
                # f"\nExtra info was: {extra_info}, which has been copied to the clipboard.\n"
            )
            new_extra_info = input(
                'Enter "b" to cancel the operation. Replace extra info with:\n'
            )
        if new_extra_info == "b":
            return edit_fields(question, answer, extra_info, extra_info)
        else:
            extra_info = new_extra_info
            extra_info = extra_info.replace("\\n", "\n")  # to handle added new lines

    print_card_preview(question, answer, hint, extra_info)

    return edit_fields(question, answer, hint, extra_info)


def confirm_with_user(prompt="") -> bool:
    """Confirms choices with the user using the given prompt."""

    print(prompt)

    y_or_n = input("[y/n] ")
    if y_or_n == "y":
        return True
    elif y_or_n == "n":
        return False
    else:
        return confirm_with_user()


def make_custom_card() -> dict[str, any]:
    """Allows the user to make a custom card."""
    ###!! needs a major refactoring (flashcard creator module)
    question, answer, hint, extra_info = "", "", "", ""

    question, answer, hint, extra_info = edit_fields(question, answer, hint, extra_info)

    card = {
        "Question": question,
        "Answer": answer,
        "Hint": hint,
        "Extra Info": extra_info,
    }

    card["is_easy"] = confirm_with_user("\nIs this an easy card?")

    card["Title"] = input("\nPlease enter Page Title: ")
    card["URL"] = input("\nPlease enter URL: ")

    return [card]


def edit_flashcards(flashcards: pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    """Allows the user to edit previously made flashcards."""

    while True:

        flashcard_number = choose_flashcard_to_edit(flashcards)

        if flashcard_number == -1:
            break

        old_card = flashcards.loc[flashcard_number]

        question = old_card["Question"]
        answer = old_card["Answer"]
        hint = old_card["Hint"]
        extra_info = old_card["Extra Info"]
        is_easy = old_card["is_easy"]

        print_card_preview(question, answer, hint, extra_info)

        question, answer, hint, extra_info = edit_fields(
            question, answer, hint, extra_info
        )

        is_easy = confirm_with_user(
            f"\nFinally, is this an easy card? Before, it was {'easy' if is_easy else 'hard'}.\n"
        )

        flashcards.at[flashcard_number, "Question"] = question
        flashcards.at[flashcard_number, "Answer"] = answer
        flashcards.at[flashcard_number, "Hint"] = hint
        flashcards.at[flashcard_number, "Extra Info"] = extra_info
        flashcards.at[flashcard_number, "is_easy"] = is_easy

        print("Card edited successfully.\n")

    return flashcards


def choose_flashcard_to_edit(flashcards: pd.core.frame.DataFrame) -> int:
    """The user searches through their flashcards and chooses which one they would like to edit."""

    substring_of_question = input(
        "\nPlease type a substring of the question of the card you wish to edit. Press 'b' to stop editing.\n"
    )

    if substring_of_question == "b":
        return -1

    matching_questions = flashcards[
        flashcards.Question.str.contains(substring_of_question)
    ]

    if len(matching_questions.index) == 0:
        print("No matching questions. Please try again")
        return choose_flashcard_to_edit(flashcards)

    matching_questions_indices = matching_questions.index.tolist()
    print(matching_questions["Question"])

    while True:
        flashcard_number = input(
            "\nChoose the flashcard number would you like to edit. Press 'b' to cancel.\n"
        )

        if flashcard_number == "b":
            return choose_flashcard_to_edit(flashcards)

        try:
            flashcard_number = int(flashcard_number)
        except:
            # if parsing to an integer fails
            print("Please choose a valid flashcard number.")
            continue

        if flashcard_number not in matching_questions_indices:
            print("Please choose a valid flashcard number.")
            continue
        else:
            return flashcard_number


def save_flashcards_to_csv(flashcards: pd.core.frame.DataFrame) -> None:
    """Saves all the flashcards we have created to a csv, which allows easy importing into Anki."""

    number_of_cards = len(flashcards.index)
    if number_of_cards == 0:
        print("No cards created. Exiting without saving.")
        return

    # putting flashcard fields in desired order
    flashcards = flashcards.reindex(
        columns=["Question", "Answer", "Hint", "Title", "Extra Info", "URL", "is_easy"]
    )

    # splitting into easy and normal difficulties
    easy_flashcards, normal_flashcards = split_into_easy_and_normal_flashcards(
        flashcards
    )

    # to timestamp csvs
    timestamp = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())

    number_of_easy_cards = len(easy_flashcards.index)
    if number_of_easy_cards > 0:
        file_name = f'(Easy) {timestamp} - {number_of_easy_cards} card{"s" if number_of_easy_cards > 1 else ""}'
        file_path = Path(f"./Flashcards/{file_name}.csv")
        file_path.parent.mkdir(
            exist_ok=True
        )  # making the "Flashcard" directory if we don't have it

        easy_flashcards.to_csv(
            file_path, columns=easy_flashcards.columns, header=False, index=False
        )

    number_of_normal_cards = len(normal_flashcards.index)
    if number_of_normal_cards > 0:
        file_name = f'(Normal) {timestamp} - {number_of_normal_cards} card{"s" if number_of_normal_cards > 1 else ""}'
        file_path = Path(f"./Flashcards/{file_name}.csv")
        file_path.parent.mkdir(
            exist_ok=True
        )  # making the "Flashcard" directory if we don't have it

        normal_flashcards.to_csv(
            file_path, columns=normal_flashcards.columns, header=False, index=False
        )

    print(
        f"Finished saving flashcards! Number of cards saved: {number_of_cards} ({number_of_easy_cards} easy, {number_of_normal_cards} normal)."
    )


def split_into_easy_and_normal_flashcards(
    flashcards: pd.core.frame.DataFrame,
) -> tuple[pd.core.frame.DataFrame, pd.core.frame.DataFrame]:
    """Separates flashcards into easy and normal difficulty collections."""

    easy_flashcards = flashcards[flashcards["is_easy"] == True]
    normal_flashcards = flashcards[flashcards["is_easy"] == False]

    # dropping unnecessary 'is_easy' column
    if len(easy_flashcards.index) > 0:
        easy_flashcards = easy_flashcards.drop(["is_easy"], axis=1)
    if len(normal_flashcards.index) > 0:
        normal_flashcards = normal_flashcards.drop(["is_easy"], axis=1)

    return easy_flashcards, normal_flashcards


if __name__ == "__main__":
    run_wikipedianki()
